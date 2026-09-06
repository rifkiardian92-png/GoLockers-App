[app]

title = GoLockers
package.name = golockers
package.domain = org.owner

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas

version = 1.0

requirements = python3,kivy==2.3.0

orientation = portrait

fullscreen = 0


# Permission Android
android.permissions = INTERNET


# Android SDK
android.api = 33
android.minapi = 24

# NDK
android.ndk = 25b

# Arsitektur APK
android.archs = arm64-v8a, armeabi-v7a

android.allow_backup = True


[buildozer]

log_level = 2
warn_on_root = 1
