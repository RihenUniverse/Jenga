# 13_packaging

python -m Jenga.Jenga build --no-daemon --jenga-file 13_packaging.jenga
python -m Jenga.Jenga package --jenga-file 13_packaging.jenga --platform windows --type zip --project PackApp
