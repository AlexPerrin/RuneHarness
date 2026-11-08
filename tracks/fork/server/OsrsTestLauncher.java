// Headless RSProx launcher of a test desktop (tools/track.sh desktop_start compiles it into the template once per source).
//
// Starts RSProx's ProxyService without its GUI, selects the proxy target named by -Dosrstest.target and
// launches one RuneLite session through it. It refuses any other target: the desktop test client
// must only ever reach our local OpenRune server, never Jagex. Exits when the client exits; exits 2 when its
// start throws (RSProx's own threads would keep a dead launcher alive).
//
// Run on Windows with -Duser.home=C:\osrs-test<N>\home (JAVA_TOOL_OPTIONS). -Dosrstest.portskip=<n> (default 0)
// moves this instance's ports up by n: RSProx serves jav_config on 43600+n and proxies on proxy.port.min (43701)+n.
// -Dosrstest.token=true: a token login; the client inherits JX_SESSION_ID, JX_CHARACTER_ID and JX_DISPLAY_NAME
// (set by track.sh) and fetches its token from the sign-in jav_config param 11 names (the server's embedded Central). A Jagex access or
// refresh token is refused in every mode. OPENRUNE_ENDPOINT (set by track.sh, http(s)://127.0.0.1:<port>) is our server's HTTP
// front: the target's jav_config must be its jav_config.ws, and that jav_config names every other endpoint.

import io.netty.buffer.ByteBufAllocator;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import net.rsprox.cache.api.CacheProvider;
import net.rsprox.proxy.ProxyService;
import net.rsprox.proxy.preferences.ClientPreferences;
import net.rsprox.proxy.preferences.ClientPreferencesFile;
import net.rsprox.proxy.binary.BinaryHeader;
import net.rsprox.proxy.target.ProxyTarget;
import net.rsprox.proxy.target.ProxyTargetConfig;
import net.rsprox.proxy.util.ProgressCallback;
import net.rsprox.shared.SessionMonitor;
import net.rsprox.shared.property.RootProperty;

public final class OsrsTestLauncher
{
	static final String TARGET = System.getProperty("osrstest.target", "OpenRune Test");

	static void log(String s)
	{
		System.out.println("[osrs-test] " + s);
		System.out.flush();
	}

	static void die(String s)
	{
		log("REFUSING: " + s);
		System.exit(2);
	}

	public static void main(String[] args)
	{
		try
		{
			run();
		}
		catch (Throwable e)
		{
			e.printStackTrace();
			die("launcher failed: " + e); // RSProx's own threads would keep a dead launcher alive
		}
	}

	static void run() throws Exception
	{
		String home = System.getProperty("user.home");
		log("user.home=" + home);
		if (!home.replace('\\', '/').toLowerCase().matches("c:/osrs-test[0-9]*/.*"))
		{
			die("user.home is not under C:\\osrs-test or C:\\osrs-test<N> (isolation not active)");
		}
		if (System.getenv("RSPS_JAVCONFIG_URL") != null || System.getenv("RSPS_RSA") != null)
		{
			die("RSPS_* overrides are set");
		}
		String endpoint = System.getenv("OPENRUNE_ENDPOINT");
		if (endpoint == null || !endpoint.matches("https?://(127\\.0\\.0\\.1|localhost):[0-9]+"))
		{
			die("OPENRUNE_ENDPOINT is not a local http(s)://127.0.0.1:<port>: " + endpoint);
		}
		boolean token = Boolean.getBoolean("osrstest.token");
		for (String v : new String[]{"JX_ACCESS_TOKEN", "JX_REFRESH_TOKEN", "JX_SESSION_ID", "JX_CHARACTER_ID", "JX_DISPLAY_NAME"})
		{
			boolean session = v.equals("JX_SESSION_ID") || v.equals("JX_CHARACTER_ID") || v.equals("JX_DISPLAY_NAME");
			if (token && session ? System.getenv(v) == null : System.getenv(v) != null)
			{
				die("Jagex launcher variable " + v + (token && session ? " is not set for a token login" : " is set"));
			}
		}

		// a fresh home's login screen opens on the terms page (a click, no key) and its Existing User on the Jagex Account prompt
		// (whose other button opens a Jagex page): its preferences hold the terms accepted (acceptedTOSVersion 1, RSProx's own)
		// and the prompt shown today (lastJagexAccountPromptRuneDay: days since 2002-02-27), as a home that has seen both
		Path prefs = ClientPreferencesFile.INSTANCE.getDEFAULT_PATH();
		if (!Files.exists(prefs))
		{
			ClientPreferencesFile.INSTANCE.write(new ClientPreferences(false, false, 1, Map.of(), null, false, 0.8, 127, 127, 127, 1, false, 25, 0, false,
				(int) (LocalDate.now(ZoneOffset.UTC).toEpochDay() - 11745)), 241, prefs);
			log("terms accepted in " + prefs);
		}

		ProxyService service = new ProxyService(ByteBufAllocator.DEFAULT);
		service.start(null, null, new ProgressCallback()
		{
			@Override
			public void update(double p, String a, String sub, String t)
			{
				log(String.format("start %3.0f%% %s", p * 100, sub));
			}

			@Override
			public void update(double p, String a, String sub)
			{
				update(p, a, sub, null);
			}
		});

		List<ProxyTargetConfig> targets = service.getProxyTargets();
		int index = -1;
		for (int i = 0; i < targets.size(); i++)
		{
			ProxyTargetConfig c = targets.get(i);
			log("target " + i + ": id=" + c.getId() + " name=" + c.getName() + " jav_config=" + c.getJavConfigUrl());
			if (TARGET.equals(c.getName()))
			{
				if (index != -1)
				{
					die("more than one target named " + TARGET);
				}
				index = i;
			}
		}
		if (index < 0)
		{
			die("no proxy target named " + TARGET + " in ~/.rsprox/proxy-targets.yaml");
		}
		ProxyTargetConfig cfg = targets.get(index);
		if (cfg.getId() == 0 || !cfg.getJavConfigUrl().equals(endpoint + "/jav_config.ws") || cfg.getModulus() == null)
		{
			die("target " + TARGET + " is not OPENRUNE_ENDPOINT's jav_config with its own modulus: " + cfg);
		}
		service.setSelectedProxyTarget(index);
		if (service.getSelectedProxyTarget() != index)
		{
			die("could not select " + TARGET);
		}

		// RSProx's HTTP port is 43600 + (proxy port - first proxy port); burning ports moves both.
		int skip = Integer.getInteger("osrstest.portskip", 0);
		if (skip < 0)
		{
			die("osrstest.portskip out of range: " + skip);
		}
		for (int i = 0; i < skip; i++)
		{
			service.allocatePort();
		}
		int port = service.allocatePort();
		ProxyTarget target = service.initializeHttpServer(port);
		if (target.getConfig() != cfg)
		{
			die("initialized target is not " + TARGET);
		}
		log("proxy port " + port + ", jav_config http://127.0.0.1:" + target.getHttpPort() + " -> " + cfg.getJavConfigUrl());
		service.launchRuneLiteClient(new Monitor(), null, port, target);
		log("RuneLite launched");

		// Exit with the client: RSProx's own threads would keep us alive otherwise.
		long idleSince = -1;
		while (true)
		{
			TimeUnit.SECONDS.sleep(5);
			boolean alive = ProcessHandle.current().descendants().anyMatch(ProcessHandle::isAlive);
			if (alive)
			{
				idleSince = -1;
				continue;
			}
			if (idleSince < 0)
			{
				idleSince = System.nanoTime();
			}
			else if (System.nanoTime() - idleSince > TimeUnit.SECONDS.toNanos(10))
			{
				log("client exited; shutting down");
				service.safeShutdown();
				System.exit(0);
			}
		}
	}

	static final class Monitor implements SessionMonitor<BinaryHeader>
	{
		@Override
		public SessionMonitor<BinaryHeader> forSession(BinaryHeader header)
		{
			return this;
		}

		@Override
		public void onLogin(BinaryHeader header)
		{
			log("login: " + header);
		}

		@Override
		public void onLogout(BinaryHeader header)
		{
			log("logout");
		}

		@Override
		public void onCacheUpdate(CacheProvider cacheProvider)
		{
		}

		@Override
		public void onIncomingBytesPerSecondUpdate(long b)
		{
		}

		@Override
		public void onOutgoingBytesPerSecondUpdate(long b)
		{
		}

		@Override
		public void onNameUpdate(String name)
		{
			log("name: " + name);
		}

		@Override
		public void onUserInformationUpdate(long userId, long userHash)
		{
		}

		@Override
		public void onTranscribe(int cycle, RootProperty property)
		{
		}
	}
}
