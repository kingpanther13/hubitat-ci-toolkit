package support

import me.biocomp.hubitat_ci.app.HubitatAppSandbox
import me.biocomp.hubitat_ci.app.HubitatAppScript
import me.biocomp.hubitat_ci.validation.Flags
import me.biocomp.hubitat_ci.util.DoNotCallMeBinding
import java.lang.reflect.Modifier

/** One entry point for the active v3.1 app, with fresh HubitatCI wiring per instance. */
class WatchdogV31Factory {
    private static final String SOURCE = new File('watchdog/e2e-deadman-watchdog-v3-1.groovy').getText('UTF-8')
    private static int compilationCount = 0
    private static final Object COMPILE_LOCK = new Object()
    private static Class<HubitatAppScript> compiledClass
    private static final Map<java.lang.reflect.Field, Map> initialMaps = [:]

    static HubitatAppScript create(Map options) {
        new HubitatAppSandbox(SOURCE).run(options + [validator: new WatchdogValidator()])
    }

    static int getCompilations() { compilationCount }

    static void resetSharedState() {
        synchronized (COMPILE_LOCK) {
            if (compiledClass == null) return
            GroovySystem.metaClassRegistry.removeMetaClass(compiledClass)
            initialMaps.each { field, initial ->
                Map current = field.get(null) as Map
                current.clear()
                current.putAll(initial)
            }
        }
    }

    private static class WatchdogValidator extends PassThroughAppValidator {
        WatchdogValidator() {
            super([Flags.DontValidatePreferences, Flags.DontValidateDefinition,
                   Flags.DontRestrictGroovy, Flags.DontRunScript])
        }

        @Override
        HubitatAppScript parseScript(String source, String name = 'Script1') {
            synchronized (COMPILE_LOCK) {
                if (compiledClass == null) {
                    HubitatAppScript first = super.parseScript(source, name)
                    compiledClass = first.getClass()
                    compilationCount++
                    // Capture initial Map contents before HubitatCI wires any test API.
                    // Keep the original Map objects and lock identities for peer instances.
                    compiledClass.declaredFields.findAll {
                        Modifier.isStatic(it.modifiers) && Map.isAssignableFrom(it.type)
                    }.each { field ->
                        field.accessible = true
                        initialMaps[field] = new LinkedHashMap(field.get(null) as Map)
                    }
                    return first
                }
                HubitatAppScript fresh = compiledClass.getDeclaredConstructor().newInstance()
                fresh.setBinding(new DoNotCallMeBinding())
                return fresh
            }
        }
    }
}
