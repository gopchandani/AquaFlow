P4APPRUNNER=./utils/p4apprunner.py
mkdir -p build
mv p4app.$1.json p4app.json
tar -czf build/p4app.tgz * --exclude='build'
#cd build
sudo python $P4APPRUNNER p4app.tgz --build-dir ./build
