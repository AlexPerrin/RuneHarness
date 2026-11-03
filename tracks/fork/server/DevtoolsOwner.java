// The owner check of a test desktop's devtools endpoint (tools/track.sh desktop_start compiles it into the template once per
// source into a jar and names it in every JVM of the instance through JAVA_TOOL_OPTIONS, as -javaagent: the one option that puts
// a class on the system class path the JDK loads a provider from, which the client's own -cp and a boot class path cannot).
//
// The JDK's HttpServer provider, -Dcom.sun.net.httpserver.HttpServerProvider=DevtoolsOwner: its servers are the JDK's own,
// each context filtered on the devtools port of -Dosrstest.devtools=<port>:<guard file>. The guard file, read on every request,
// holds the token of the up that started the instance (its state/<slug>/up.json): a request is answered only when it carries
// "Authorization: Bearer <token>", any other gets 401. An empty guard answers any caller: desktop_login.py writes it empty
// while a session's desktop bridge predates mcp/serve.py (it sends no token) and the token again once none lives, so a live
// desktop follows that fact. The devtools plugin binds 127.0.0.1, which every local process reaches: the token is what makes
// the endpoint answer its owner alone. Requests to any other port pass unchanged.
// The plugin interrupts the active tool on every tools/call (it assumes one caller), and the owner has two (the run and its
// keeper, desktop_login.py keep): tools/call requests run one at a time, in arrival order, so no call preempts another; a
// notification (notifications/cancelled) passes at once, so a caller's cancel still reaches its call.
// Every tools/call is answered within WAIT past its own timeoutMs, its wait for the call ahead included: the handler answers
// into a buffer, and a handler that has not returned by then (a hung plugin, a stream that never ends) is answered with an
// error, whatever bridge sent the call; the call is left to the plugin, which the next call interrupts.

import com.sun.net.httpserver.Filter;
import com.sun.net.httpserver.HttpContext;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpsServer;
import com.sun.net.httpserver.spi.HttpServerProvider;
import com.sun.net.httpserver.Headers;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.locks.ReentrantLock;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class DevtoolsOwner extends HttpServerProvider
{
	static final String[] OWNER = System.getProperty("osrstest.devtools", "").split(":", 2);

	public static void premain(String args)
	{
	}

	final HttpServerProvider jdk = new sun.net.httpserver.DefaultHttpServerProvider();

	@Override
	public HttpServer createHttpServer(InetSocketAddress addr, int backlog) throws IOException
	{
		return new Owned(jdk.createHttpServer(addr, backlog));
	}

	@Override
	public HttpsServer createHttpsServer(InetSocketAddress addr, int backlog) throws IOException
	{
		return jdk.createHttpsServer(addr, backlog);
	}

	static final ReentrantLock ONE = new ReentrantLock(true);
	static final Pattern CALL = Pattern.compile("\"method\"\\s*:\\s*\"tools/call\"");

	static final long WAIT = 20_000;   // ms past a call's timeoutMs the endpoint has to answer it: below the bridge's ANSWER_WAIT, so its answer comes first
	static final Pattern TIMEOUT = Pattern.compile("\"timeoutMs\"\\s*:\\s*(\\d+)");
	static final Pattern ID = Pattern.compile("\"id\"\\s*:\\s*(\"[^\"]*\"|-?\\d+)");

	static void answer(HttpExchange x, int code, String contentType, byte[] b) throws IOException
	{
		x.getResponseHeaders().set("Content-Type", contentType);
		x.sendResponseHeaders(code, b.length == 0 ? -1 : b.length);
		if (b.length > 0)
		{
			x.getResponseBody().write(b);
		}
		x.close();
	}

	static void refuse(HttpExchange x, String why) throws IOException
	{
		x.getRequestBody().readAllBytes();
		answer(x, 401, "application/json", ("{\"jsonrpc\":\"2.0\",\"id\":null,\"error\":{\"code\":-32001,\"message\":\"" + why + "\"}}").getBytes(StandardCharsets.UTF_8));
	}

	static final Filter GATE = new Filter()
	{
		@Override
		public void doFilter(HttpExchange x, Chain chain) throws IOException
		{
			if (OWNER.length < 2 || x.getLocalAddress().getPort() != Integer.parseInt(OWNER[0]))
			{
				chain.doFilter(x);
				return;
			}
			String token;
			try
			{
				token = Files.readString(Path.of(OWNER[1])).trim();
			}
			catch (IOException e)
			{
				refuse(x, "this desktop has no guard file " + OWNER[1].replace("\\", "/") + ": tools/track.sh up writes it");
				return;
			}
			String auth = String.valueOf(x.getRequestHeaders().getFirst("Authorization"));
			if (!token.isEmpty() && !MessageDigest.isEqual(("Bearer " + token).getBytes(StandardCharsets.UTF_8), auth.getBytes(StandardCharsets.UTF_8)))
			{
				refuse(x, "this desktop answers only the up that started it: send Authorization: Bearer <token>, the token of your change's state/<slug>/up.json");
				return;
			}
			byte[] body = x.getRequestBody().readAllBytes();
			String text = new String(body, StandardCharsets.UTF_8);
			if (!CALL.matcher(text).find())
			{
				x.setStreams(new ByteArrayInputStream(body), null);
				chain.doFilter(x);
				return;
			}
			Matcher t = TIMEOUT.matcher(text), id = ID.matcher(text);
			long bound = WAIT + (t.find() ? Long.parseLong(t.group(1)) : 0), end = System.nanoTime() + bound * 1_000_000;
			Buffered b = new Buffered(x, body);
			boolean held = false;
			try
			{
				held = ONE.tryLock(bound, TimeUnit.MILLISECONDS);
				if (held)
				{
					Thread w = new Thread(() ->
					{
						try
						{
							chain.doFilter(b);
						}
						catch (Throwable e)
						{
							b.fail = e;
						}
						finally
						{
							b.done.complete(null);
						}
					}, "devtools-call");
					w.setDaemon(true);
					w.start();
					b.done.get(Math.max(0, end - System.nanoTime()), TimeUnit.NANOSECONDS);
				}
			}
			catch (TimeoutException | InterruptedException | java.util.concurrent.ExecutionException e)
			{
				// answered below as no answer
			}
			finally
			{
				if (held)
				{
					ONE.unlock();
				}
			}
			synchronized (b)
			{
				b.closed = true;   // a late handler writes into a buffer no one reads
				if (b.done.isDone() && b.fail == null && b.code > 0)
				{
					b.responseHeaders.forEach((k, v) ->
					{
						if (!k.equalsIgnoreCase("Content-length") && !k.equalsIgnoreCase("Transfer-encoding"))
						{
							x.getResponseHeaders().put(k, v);
						}
					});
					byte[] r = b.out.toByteArray();
					x.sendResponseHeaders(b.code, r.length == 0 ? -1 : r.length);
					if (r.length > 0)
					{
						x.getResponseBody().write(r);
					}
					x.close();
					return;
				}
			}
			String why = b.fail != null ? "the desktop's devtools failed on the call: " + b.fail
				: (held ? "the desktop did not answer the call within " : "a call ahead held the desktop past ") + bound / 1000 + " s"
				+ " (its plugin hung: tools/track.sh restart <slug>, or down and up)";
			answer(x, 200, "application/json", ("{\"jsonrpc\":\"2.0\",\"id\":" + (id.find() ? id.group(1) : "null")
				+ ",\"error\":{\"code\":-32002,\"message\":\"" + why.replace("\\", "/").replace("\"", "'") + "\"}}").getBytes(StandardCharsets.UTF_8));
		}

		@Override
		public String description()
		{
			return "devtools owner";
		}
	};

	// the exchange a tools/call's handler answers into: the request as read, its response held until the filter sends it
	static final class Buffered extends HttpExchange
	{
		final HttpExchange x;
		final byte[] body;
		final Headers responseHeaders = new Headers();
		final CompletableFuture<Void> done = new CompletableFuture<>();
		final ByteArrayOutputStream out = new ByteArrayOutputStream()
		{
			@Override
			public synchronized void write(byte[] b, int off, int len)
			{
				if (!closed)
				{
					super.write(b, off, len);
				}
			}

			@Override
			public synchronized void write(int b)
			{
				if (!closed)
				{
					super.write(b);
				}
			}
		};
		InputStream in;
		volatile boolean closed;
		volatile int code;
		volatile Throwable fail;

		Buffered(HttpExchange x, byte[] body)
		{
			this.x = x;
			this.body = body;
			this.in = new ByteArrayInputStream(body);
		}

		@Override public Headers getRequestHeaders() { return x.getRequestHeaders(); }
		@Override public Headers getResponseHeaders() { return responseHeaders; }
		@Override public URI getRequestURI() { return x.getRequestURI(); }
		@Override public String getRequestMethod() { return x.getRequestMethod(); }
		@Override public HttpContext getHttpContext() { return x.getHttpContext(); }
		@Override public void close() { }
		@Override public InputStream getRequestBody() { return in; }
		@Override public OutputStream getResponseBody() { return out; }
		@Override public void sendResponseHeaders(int rCode, long len) { code = rCode; }
		@Override public InetSocketAddress getRemoteAddress() { return x.getRemoteAddress(); }
		@Override public int getResponseCode() { return code; }
		@Override public InetSocketAddress getLocalAddress() { return x.getLocalAddress(); }
		@Override public String getProtocol() { return x.getProtocol(); }
		@Override public Object getAttribute(String name) { return x.getAttribute(name); }
		@Override public void setAttribute(String name, Object value) { x.setAttribute(name, value); }
		@Override public void setStreams(InputStream i, OutputStream o) { if (i != null) in = i; }
		@Override public com.sun.net.httpserver.HttpPrincipal getPrincipal() { return x.getPrincipal(); }
	}

	static final class Owned extends HttpServer
	{
		final HttpServer s;

		Owned(HttpServer s)
		{
			this.s = s;
		}

		static HttpContext gated(HttpContext c)
		{
			c.getFilters().add(GATE);
			return c;
		}

		@Override public void bind(InetSocketAddress addr, int backlog) throws IOException { s.bind(addr, backlog); }
		@Override public void start() { s.start(); }
		@Override public void setExecutor(Executor e) { s.setExecutor(e); }
		@Override public Executor getExecutor() { return s.getExecutor(); }
		@Override public void stop(int delay) { s.stop(delay); }
		@Override public HttpContext createContext(String path, HttpHandler h) { return gated(s.createContext(path, h)); }
		@Override public HttpContext createContext(String path) { return gated(s.createContext(path)); }
		@Override public void removeContext(String path) { s.removeContext(path); }
		@Override public void removeContext(HttpContext c) { s.removeContext(c); }
		@Override public InetSocketAddress getAddress() { return s.getAddress(); }
	}
}
