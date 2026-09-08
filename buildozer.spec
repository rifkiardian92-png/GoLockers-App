[app]

title = GoLockers
package.name = golockers
package.domain = org.owner

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas

version = 1.0

# Gunakan Kivy 2.3.0 (versi terbaru yang stabil)
requirements = python3,kivy==2.3.0

orientation = portrait

fullscreen = 0

# Permission Android
android.permissions = INTERNET

# Android SDK
android.api = 33
android.minapi = 24
android.build_tools_version = 33.0.2

# NDK
android.ndk = 24.0.8215888

# License Agreement
android.accept_sdk_license = True

# Arsitektur APK
android.archs = arm64-v8a, armeabi-v7a

android.allow_backup = True

# Python version
python.version = 3.10


[buildozer]

log_level = 2
warn_on_root = 1
