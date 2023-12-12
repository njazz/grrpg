cd $( dirname -- "$0"; )
cd ..

pyinstaller --onefile --noupx --windowed --noconsole grrpg_app.py --paths ./grrpg/

rm -rf build/
rm -rf grrpg/__pycache__

# --target-architecture=universal2 