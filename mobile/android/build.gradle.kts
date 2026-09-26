allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

val newBuildDir: Directory =
    rootProject.layout.buildDirectory
        .dir("../../build")
        .get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}

// Плагины (file_picker и др.) по умолчанию на compileSdk 34, а lifecycle требует 36.
subprojects {
    fun forceCompileSdk36() {
        val android = extensions.findByName("android") ?: return
        try {
            val setCompileSdk =
                android.javaClass.methods.firstOrNull {
                    it.name == "setCompileSdk" && it.parameterCount == 1
                }
            if (setCompileSdk != null) {
                setCompileSdk.invoke(android, 36)
                return
            }
            val setCompileSdkVersion =
                android.javaClass.methods.firstOrNull {
                    it.name == "setCompileSdkVersion" && it.parameterCount == 1
                }
            setCompileSdkVersion?.invoke(android, 36)
        } catch (_: Exception) {
            // ignore
        }
    }

    if (state.executed) {
        forceCompileSdk36()
    } else {
        afterEvaluate { forceCompileSdk36() }
    }
}

subprojects {
    project.evaluationDependsOn(":app")
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
