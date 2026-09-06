[app]
title = GoLockers
package.name = golockers
package.domain = org.owner
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.2.1
orientation = portrait
fullscreen = 0
android.permissions = android.permission.INTERNET
android.api = 33
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
