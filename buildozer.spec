[app]

title = GoLockers
package.name = golockers
package.domain = org.owner

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas

version = 1.0

# UBAH KE KIVY 2.2.1 (lebih stabil)
requirements = python3,kivy==2.2.1

orientation = portrait

fullscreen = 0

# Permission Android
android.permissions = INTERNET

# Android SDK
android.api = 33
android.minapi = 24
android.build_tools_version = 33.0.2

# NDK
android.ndk = 25b

# License Agreement
android.accept_sdk_license = True

# Arsitektur APK
android.archs = arm64-v8a, armeabi-v7a

android.allow_backup = True

# UBAH KE PYTHON 3.10 (lebih kompatibel)
python.version = 3.10


[buildozer]

log_level = 2
warn_on_root = 1
