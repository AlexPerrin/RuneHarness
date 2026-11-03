import java.lang.reflect.Method;
import java.lang.reflect.Modifier;

/**
 * Prints "iface impl implemented total" for each RuneLite API interface the plugin host backs.
 * A method counts as implemented when the host class (or a non-generated superclass) declares
 * it; methods that resolve to a generated *Stub/*Bag class throw or are inert, so they don't count.
 * Run by tools/progress.py with re/host/classes + the RuneLite jars + android.jar on the class path.
 */
public class ApiCoverage {
    public static void main(String[] args) throws Exception {
        for (int i = 0; i + 1 < args.length; i += 2) {
            // Load without initializing: host classes' static initializers may call into Native,
            // which has no library on the desktop JVM.
            ClassLoader cl = ApiCoverage.class.getClassLoader();
            Class<?> iface = Class.forName("net.runelite.api." + args[i], false, cl);
            Class<?> impl = Class.forName("net.runelite.host." + args[i + 1], false, cl);
            int total = 0, done = 0;
            StringBuilder missing = new StringBuilder();
            for (Method m : iface.getMethods()) {
                if (!Modifier.isAbstract(m.getModifiers())) continue;
                total++;
                String owner = impl.getMethod(m.getName(), m.getParameterTypes()).getDeclaringClass().getSimpleName();
                if (owner.endsWith("Stub") || owner.endsWith("Bag")) missing.append(' ').append(m.getName());
                else done++;
            }
            System.out.println(args[i] + " " + args[i + 1] + " " + done + " " + total + missing);
        }
    }
}
