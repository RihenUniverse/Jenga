#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jenga Build System - Enhanced Android Support
Complete Android build system with Gradle, AAB, Multi-ABI, ProGuard, etc.
"""

import os
import subprocess
import shutil
import json
from pathlib import Path
from typing import Optional, List, Dict

try:
    from ..utils.display import Display
    from ..utils.reporter import Reporter
except ImportError:
    from utils.display import Display
    from utils.reporter import Reporter


class AndroidBuilder:
    """Enhanced Android build system with full Gradle support"""
    
    def __init__(self, workspace, project, config: str):
        self.workspace = workspace
        self.project = project
        self.config = config
        
        # Validate paths
        self.sdk_path = Path(workspace.androidsdkpath) if workspace.androidsdkpath else None
        self.ndk_path = Path(workspace.androidndkpath) if workspace.androidndkpath else None
        self.jdk_path = Path(workspace.javajdkpath) if hasattr(workspace, 'javajdkpath') and workspace.javajdkpath else None
        
        if not self.sdk_path:
            raise RuntimeError("Android SDK path not configured (use androidsdkpath)")
        if not self.ndk_path:
            raise RuntimeError("Android NDK path not configured (use androidndkpath)")
        
        # App configuration
        self.package_name = getattr(project, 'androidapplicationid', f'com.example.{project.name.lower()}')
        self.min_sdk = getattr(project, 'androidminsdk', 21)
        self.target_sdk = getattr(project, 'androidtargetsdk', 33)
        self.compile_sdk = getattr(project, 'androidcompilesdk', self.target_sdk)
        self.version_code = getattr(project, 'androidversioncode', 1)
        self.version_name = getattr(project, 'androidversionname', '1.0')
        self.ndk_version = getattr(project, 'ndkversion', '25.1.8937393')
        
        # Multi-ABI configuration
        self.abis = getattr(project, 'androidabis', ['armeabi-v7a', 'arm64-v8a', 'x86', 'x86_64'])
        
        # ProGuard configuration
        self.use_proguard = getattr(project, 'androidproguard', False)
        self.proguard_rules = getattr(project, 'androidproguardrules', [])
        
        # Assets configuration
        self.assets_dirs = getattr(project, 'androidassets', [])
        
        # Permissions configuration
        self.permissions = getattr(project, 'androidpermissions', ['INTERNET'])
        
        # Native activity vs Java activity
        self.use_native_activity = getattr(project, 'androidnativeactivity', True)
        
        # Build directories
        self.build_root = Path(workspace.location) / "Build" / "Android" / config
        self.gradle_project_dir = self.build_root / "GradleProject"
    
    def create_gradle_project(self) -> bool:
        """Create complete Gradle project structure"""
        
        Reporter.info("Creating Gradle project structure...")
        
        app_dir = self.gradle_project_dir / "app"
        app_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Root build.gradle
        self._create_root_build_gradle()
        
        # 2. settings.gradle
        self._create_settings_gradle()
        
        # 3. gradle.properties
        self._create_gradle_properties()
        
        # 4. App build.gradle (with AAB and ProGuard support)
        self._create_app_build_gradle(app_dir)
        
        # 5. AndroidManifest.xml (with dynamic permissions)
        self._create_android_manifest(app_dir)
        
        # 6. MainActivity (if needed)
        if not self.use_native_activity:
            self._create_main_activity(app_dir)
        
        # 7. CMakeLists.txt for native code (Multi-ABI support)
        self._create_cmakelists(app_dir)
        
        # 8. Copy native sources
        self._copy_native_sources(app_dir)
        
        # 9. Resources
        self._create_resources(app_dir)
        
        # 10. ProGuard rules
        if self.use_proguard:
            self._create_proguard_rules(app_dir)
        
        # 11. Copy assets
        if self.assets_dirs:
            self._copy_assets(app_dir)
        
        # 12. Gradle wrapper
        self._setup_gradle_wrapper()
        
        Display.success("✓ Gradle project created")
        
        return True
    
    def _create_app_build_gradle(self, app_dir: Path):
        """Create app/build.gradle with AAB and ProGuard support"""
        
        # ProGuard configuration
        proguard_config = ""
        if self.use_proguard:
            proguard_config = """
            minifyEnabled true
            shrinkResources true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
"""
        else:
            proguard_config = """
            minifyEnabled false
"""
        
        # ABI filters
        abi_filters = ', '.join(f"'{abi}'" for abi in self.abis)
        
        content = f"""plugins {{
    id 'com.android.application'
}}

android {{
    namespace '{self.package_name}'
    compileSdk {self.compile_sdk}
    ndkVersion '{self.ndk_version}'
    
    defaultConfig {{
        applicationId "{self.package_name}"
        minSdk {self.min_sdk}
        targetSdk {self.target_sdk}
        versionCode {self.version_code}
        versionName "{self.version_name}"
        
        ndk {{
            abiFilters {abi_filters}
        }}
        
        externalNativeBuild {{
            cmake {{
                cppFlags "-std=c++17"
                arguments "-DANDROID_STL=c++_shared"
                
                // Multi-ABI support
                abiFilters {abi_filters}
            }}
        }}
    }}
    
    buildTypes {{
        release {{
            {proguard_config}
        }}
        debug {{
            debuggable true
            minifyEnabled false
        }}
    }}
    
    // Multi-ABI splits (optional - for separate APKs per ABI)
    splits {{
        abi {{
            enable true
            reset()
            include {abi_filters}
            universalApk true
        }}
    }}
    
    externalNativeBuild {{
        cmake {{
            path file('src/main/cpp/CMakeLists.txt')
            version '3.22.1'
        }}
    }}
    
    compileOptions {{
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }}
    
    // Bundle configuration for AAB
    bundle {{
        language {{
            enableSplit = false
        }}
        density {{
            enableSplit = true
        }}
        abi {{
            enableSplit = true
        }}
    }}
}}

dependencies {{
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'com.google.android.material:material:1.9.0'
}}
"""
        
        (app_dir / "build.gradle").write_text(content)
        (app_dir / "proguard-rules.pro").touch()
    
    def _create_android_manifest(self, app_dir: Path):
        """Create AndroidManifest.xml with dynamic permissions"""
        
        manifest_dir = app_dir / "src" / "main"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        
        # Build permissions section
        permissions_xml = ""
        for perm in self.permissions:
            # Handle both short names and full names
            if not perm.startswith("android.permission."):
                perm_full = f"android.permission.{perm}"
            else:
                perm_full = perm
            
            permissions_xml += f'\n    <uses-permission android:name="{perm_full}" />'
        
        # Choose activity type
        if self.use_native_activity:
            # Pure native app
            activity_xml = f"""
        <activity
            android:name="android.app.NativeActivity"
            android:label="{self.project.name}"
            android:configChanges="orientation|keyboardHidden|screenSize"
            android:exported="true">
            
            <meta-data
                android:name="android.app.lib_name"
                android:value="{self.project.name.lower()}" />
            
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
"""
        else:
            # Java activity with JNI
            activity_xml = f"""
        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
"""
        
        content = f"""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    {permissions_xml}
    
    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="{self.project.name}"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.AppCompat.Light.DarkActionBar"
        android:hasCode="{str(not self.use_native_activity).lower()}"
        android:debuggable="{str(self.config == 'Debug').lower()}">
        {activity_xml}
    </application>
</manifest>
"""
        
        (manifest_dir / "AndroidManifest.xml").write_text(content)
    
    def _create_cmakelists(self, app_dir: Path):
        """Create CMakeLists.txt with Multi-ABI support"""
        
        cpp_dir = app_dir / "src" / "main" / "cpp"
        cpp_dir.mkdir(parents=True, exist_ok=True)
        
        # Get source files
        source_files = []
        if self.project.files:
            for pattern in self.project.files:
                source_files.append(pattern.replace('**/', '').replace('*.cpp', ''))
        
        if not source_files:
            source_files = ['native-lib.cpp']
        
        content = f"""# CMakeLists.txt - Generated by Jenga Build System
cmake_minimum_required(VERSION 3.22.1)

project("{self.project.name}")

# C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Multi-ABI support
set(CMAKE_ANDROID_ARCH_ABI ${{ANDROID_ABI}})

# Source files
add_library({self.project.name.lower()} SHARED
"""
        
        for src in source_files:
            content += f"    {src}\n"
        
        content += """)

# Include directories
target_include_directories(${{PROJECT_NAME}} PRIVATE
"""
        
        if self.project.includedirs:
            for inc in self.project.includedirs:
                content += f"    ${{CMAKE_CURRENT_SOURCE_DIR}}/../../../{inc}\n"
        
        content += """)

# Find required libraries
find_library(log-lib log)
find_library(android-lib android)

# Link libraries
target_link_libraries(${{PROJECT_NAME}}
    ${{log-lib}}
    ${{android-lib}}
"""
        
        if self.project.links:
            for lib in self.project.links:
                content += f"    {lib}\n"
        
        content += """)

# Defines
target_compile_definitions(${{PROJECT_NAME}} PRIVATE
    ANDROID
    __ANDROID__
    ANDROID_ABI_${{ANDROID_ABI}}
"""
        
        if self.project.defines:
            for define in self.project.defines:
                content += f"    {define}\n"
        
        content += """)

# ABI-specific optimizations
if(ANDROID_ABI STREQUAL "armeabi-v7a")
    target_compile_options(${{PROJECT_NAME}} PRIVATE -mfpu=neon)
elseif(ANDROID_ABI STREQUAL "arm64-v8a")
    target_compile_options(${{PROJECT_NAME}} PRIVATE -march=armv8-a)
endif()
"""
        
        (cpp_dir / "CMakeLists.txt").write_text(content)
    
    def _create_proguard_rules(self, app_dir: Path):
        """Create ProGuard rules file"""
        
        rules_file = app_dir / "proguard-rules.pro"
        
        # Default rules
        default_rules = """# Jenga Build System - ProGuard Rules

# Keep native methods
-keepclasseswithmembernames class * {
    native <methods>;
}

# Keep custom rules from project
"""
        
        # Add custom rules from project
        custom_rules = "\n".join(self.proguard_rules)
        
        content = default_rules + custom_rules
        
        rules_file.write_text(content)
        
        Display.info(f"  ProGuard rules created with {len(self.proguard_rules)} custom rules")
    
    def _copy_assets(self, app_dir: Path):
        """Copy assets to Android assets directory"""
        
        assets_dest = app_dir / "src" / "main" / "assets"
        assets_dest.mkdir(parents=True, exist_ok=True)
        
        Reporter.info("Copying assets...")
        
        import shutil
        from pathlib import Path
        
        base_dir = Path(self.workspace.location)
        
        for asset_pattern in self.assets_dirs:
            # Handle wildcards
            if "*" in asset_pattern:
                # Use glob
                for asset_file in base_dir.glob(asset_pattern):
                    if asset_file.is_file():
                        dest_file = assets_dest / asset_file.name
                        shutil.copy2(asset_file, dest_file)
                        Reporter.detail(f"  Copied asset: {asset_file.name}")
                    elif asset_file.is_dir():
                        dest_dir = assets_dest / asset_file.name
                        if dest_dir.exists():
                            shutil.rmtree(dest_dir)
                        shutil.copytree(asset_file, dest_dir)
                        Reporter.detail(f"  Copied asset dir: {asset_file.name}")
            else:
                # Single file or directory
                asset_path = base_dir / asset_pattern
                
                if asset_path.exists():
                    if asset_path.is_file():
                        dest_file = assets_dest / asset_path.name
                        shutil.copy2(asset_path, dest_file)
                        Reporter.detail(f"  Copied asset: {asset_path.name}")
                    elif asset_path.is_dir():
                        dest_dir = assets_dest / asset_path.name
                        if dest_dir.exists():
                            shutil.rmtree(dest_dir)
                        shutil.copytree(asset_path, dest_dir)
                        Reporter.detail(f"  Copied asset dir: {asset_path.name}")
                else:
                    Display.warning(f"Asset not found: {asset_pattern}")
    
    def build_apk(self, build_type: str = "debug") -> Optional[Path]:
        """Build APK using Gradle"""
        
        Reporter.info(f"Building {build_type.upper()} APK with Gradle...")
        
        gradle_cmd = self._get_gradle_command()
        
        if not gradle_cmd:
            Display.error("Gradle not found")
            return None
        
        # Build task
        task = f"assemble{build_type.capitalize()}"
        
        try:
            Display.info(f"Running: {gradle_cmd} {task}")
            
            result = subprocess.run(
                [str(gradle_cmd), task, "--stacktrace"],
                cwd=self.gradle_project_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                Display.error("Gradle build failed:")
                print(result.stdout)
                print(result.stderr)
                return None
            
            Display.success("✓ Gradle build completed")
            
            # Find generated APKs (may be multiple for ABI splits)
            apk_dir = self.gradle_project_dir / "app" / "build" / "outputs" / "apk" / build_type
            apks = list(apk_dir.glob("*.apk"))
            
            if apks:
                # Copy all APKs to standard location
                output_dir = self.build_root / "Package"
                output_dir.mkdir(parents=True, exist_ok=True)
                
                main_apk = None
                
                for apk in apks:
                    dest_apk = output_dir / apk.name
                    shutil.copy2(apk, dest_apk)
                    Display.success(f"✓ APK created: {dest_apk}")
                    
                    # Universal APK is the main one
                    if "universal" in apk.name.lower() or len(apks) == 1:
                        main_apk = dest_apk
                
                return main_apk or apks[0]
            else:
                Display.error("APK not found after build")
                return None
        
        except Exception as e:
            Display.error(f"Build error: {e}")
            return None
    
    def build_aab(self) -> Optional[Path]:
        """Build AAB (Android App Bundle) using Gradle"""
        
        Reporter.info("Building AAB (Android App Bundle)...")
        
        gradle_cmd = self._get_gradle_command()
        
        if not gradle_cmd:
            Display.error("Gradle not found")
            return None
        
        # Build task for AAB
        task = "bundleRelease"
        
        try:
            Display.info(f"Running: {gradle_cmd} {task}")
            
            result = subprocess.run(
                [str(gradle_cmd), task, "--stacktrace"],
                cwd=self.gradle_project_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                Display.error("Gradle AAB build failed:")
                print(result.stdout)
                print(result.stderr)
                return None
            
            Display.success("✓ AAB build completed")
            
            # Find generated AAB
            aab_dir = self.gradle_project_dir / "app" / "build" / "outputs" / "bundle" / "release"
            aabs = list(aab_dir.glob("*.aab"))
            
            if aabs:
                aab_path = aabs[0]
                
                # Copy to standard location
                output_dir = self.build_root / "Package"
                output_dir.mkdir(parents=True, exist_ok=True)
                
                final_aab = output_dir / f"{self.project.name}-release.aab"
                shutil.copy2(aab_path, final_aab)
                
                Display.success(f"✓ AAB created: {final_aab}")
                Display.info(f"  Size: {final_aab.stat().st_size / (1024*1024):.2f} MB")
                
                return final_aab
            else:
                Display.error("AAB not found after build")
                return None
        
        except Exception as e:
            Display.error(f"AAB build error: {e}")
            return None
    
    def _get_gradle_command(self):
        """Get Gradle command (wrapper or system)"""
        
        # Check for gradlew
        if os.name == 'nt':
            gradlew = self.gradle_project_dir / "gradlew.bat"
        else:
            gradlew = self.gradle_project_dir / "gradlew"
        
        if gradlew.exists():
            # Make executable on Unix
            if os.name != 'nt':
                gradlew.chmod(0o755)
            return str(gradlew)
        
        # Check system Gradle
        gradle = shutil.which("gradle")
        if gradle:
            return gradle
        
        return None
    
    # ... (rest of the methods from previous androidsystem.py)
    # Copy all other methods like _create_root_build_gradle, _create_settings_gradle, etc.
    
    def _create_root_build_gradle(self):
        """Create root build.gradle"""
        content = f"""// Top-level build file
buildscript {{
    repositories {{
        google()
        mavenCentral()
    }}
    dependencies {{
        classpath 'com.android.tools.build:gradle:8.1.0'
    }}
}}

allprojects {{
    repositories {{
        google()
        mavenCentral()
    }}
}}

task clean(type: Delete) {{
    delete rootProject.buildDir
}}
"""
        (self.gradle_project_dir / "build.gradle").write_text(content)
    
    def _create_settings_gradle(self):
        """Create settings.gradle"""
        content = f"""rootProject.name = "{self.project.name}"
include ':app'
"""
        (self.gradle_project_dir / "settings.gradle").write_text(content)
    
    def _create_gradle_properties(self):
        """Create gradle.properties"""
        content = """org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
android.enableJetifier=true
"""
        if self.sdk_path:
            content += f"\nsdk.dir={self.sdk_path}\n"
        if self.ndk_path:
            content += f"ndk.dir={self.ndk_path}\n"
        
        (self.gradle_project_dir / "gradle.properties").write_text(content)
    
    def _create_main_activity(self, app_dir: Path):
        """Create MainActivity.java"""
        java_dir = app_dir / "src" / "main" / "java"
        package_path = self.package_name.replace('.', '/')
        activity_dir = java_dir / package_path
        activity_dir.mkdir(parents=True, exist_ok=True)
        
        content = f"""package {self.package_name};

import androidx.appcompat.app.AppCompatActivity;
import android.os.Bundle;
import android.widget.TextView;

public class MainActivity extends AppCompatActivity {{
    
    static {{
        System.loadLibrary("{self.project.name.lower()}");
    }}
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {{
        super.onCreate(savedInstanceState);
        
        TextView tv = new TextView(this);
        tv.setText(stringFromJNI());
        setContentView(tv);
    }}
    
    public native String stringFromJNI();
}}
"""
        (activity_dir / "MainActivity.java").write_text(content)
    
    def _copy_native_sources(self, app_dir: Path):
        """Copy native C++ sources"""
        cpp_dir = app_dir / "src" / "main" / "cpp"
        cpp_dir.mkdir(parents=True, exist_ok=True)
        
        if self.project.files:
            project_dir = Path(self.workspace.location) / self.project.location
            
            for pattern in self.project.files:
                for src_file in project_dir.glob(pattern):
                    if src_file.is_file():
                        dest = cpp_dir / src_file.name
                        shutil.copy2(src_file, dest)
                        Reporter.info(f"  Copied: {src_file.name}")
        
        if not list(cpp_dir.glob("*.cpp")):
            self._create_default_native_lib(cpp_dir)
    
    def _create_default_native_lib(self, cpp_dir: Path):
        """Create default native library"""
        if self.use_native_activity:
            content = """#include <android/log.h>
#include <android_native_app_glue.h>

#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, "NativeApp", __VA_ARGS__)

void android_main(struct android_app* app) {
    LOGI("App started");
    
    int events;
    struct android_poll_source* source;
    
    while (true) {
        while (ALooper_pollAll(0, nullptr, &events, (void**)&source) >= 0) {
            if (source != nullptr) {
                source->process(app, source);
            }
            
            if (app->destroyRequested != 0) {
                LOGI("App destroyed");
                return;
            }
        }
    }
}
"""
        else:
            content = f"""#include <jni.h>
#include <string>
#include <android/log.h>

#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, "{self.project.name}", __VA_ARGS__)

extern "C" JNIEXPORT jstring JNICALL
Java_{self.package_name.replace('.', '_')}_MainActivity_stringFromJNI(
        JNIEnv* env,
        jobject) {{
    std::string hello = "Hello from {self.project.name}!";
    LOGI("%s", hello.c_str());
    return env->NewStringUTF(hello.c_str());
}}
"""
        (cpp_dir / "native-lib.cpp").write_text(content)
    
    def _create_resources(self, app_dir: Path):
        """Create basic resources"""
        res_dir = app_dir / "src" / "main" / "res"
        
        (res_dir / "values").mkdir(parents=True, exist_ok=True)
        for dpi in ["mdpi", "hdpi", "xhdpi", "xxhdpi", "xxxhdpi"]:
            (res_dir / f"mipmap-{dpi}").mkdir(parents=True, exist_ok=True)
        
        strings_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">{self.project.name}</string>
</resources>
"""
        (res_dir / "values" / "strings.xml").write_text(strings_xml)
        
        colors_xml = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="colorPrimary">#6200EE</color>
    <color name="colorPrimaryDark">#3700B3</color>
    <color name="colorAccent">#03DAC5</color>
</resources>
"""
        (res_dir / "values" / "colors.xml").write_text(colors_xml)
    
    def _setup_gradle_wrapper(self):
        """Setup Gradle wrapper"""
        Reporter.info("Setting up Gradle wrapper...")
        
        gradle_cmd = shutil.which("gradle")
        
        if gradle_cmd:
            try:
                result = subprocess.run(
                    ["gradle", "wrapper", "--gradle-version", "8.0"],
                    cwd=self.gradle_project_dir,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    Display.success("✓ Gradle wrapper installed")
                else:
                    Display.warning("Could not install Gradle wrapper")
            except Exception as e:
                Display.warning(f"Gradle wrapper setup failed: {e}")
        else:
            Display.warning("Gradle not found in PATH")


def build_android_with_gradle(workspace, project, config: str, output_type: str = "apk") -> Optional[Path]:
    """Main function to build Android project"""
    
    try:
        builder = AndroidBuilder(workspace, project, config)
        
        # Step 1: Create Gradle project
        if not builder.create_gradle_project():
            return None
        
        # Step 2: Build APK or AAB
        if output_type == "aab":
            return builder.build_aab()
        else:
            return builder.build_apk(config.lower())
    
    except Exception as e:
        Display.error(f"Android build failed: {e}")
        import traceback
        traceback.print_exc()
        return None
