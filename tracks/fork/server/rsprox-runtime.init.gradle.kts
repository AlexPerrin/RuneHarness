// Gradle init script (desktop_template.sh): exports RSProx's root runtime classpath (proxy, GUI and their dependencies)
// into build/osrs-test-runtime, the classpath of the headless launcher (OsrsTestLauncher.java) on Windows.
allprojects {
    if (this == rootProject) {
        afterEvaluate {
            tasks.register<Copy>("osrsTestRuntime") {
                from(configurations.getByName("runtimeClasspath"))
                into(layout.buildDirectory.dir("osrs-test-runtime"))
            }
        }
    }
}
