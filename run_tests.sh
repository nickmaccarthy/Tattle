echo "Running python 2.7 Tests..."
echo "Python version..."
env/bin/python --version
echo ""
env/bin/python -m unittest discover -s tests/ -p '*_tests.py'
echo "Running python 3.x Tests..."
echo "Python version..."
env3.5/bin/python --version
env3.5/bin/python -m unittest discover -s tests/ -p '*_tests.py'
