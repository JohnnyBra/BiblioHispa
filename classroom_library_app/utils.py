import sys
import os

def get_data_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Not running in a bundle, so assume standard development structure
        # Assumes this utils.py is in classroom_library_app/
        # and main.py, etc., are also in classroom_library_app/ or subdirs like database/
        # So, the base path is one level up from this file's directory (the project root)
        # However, for the current setup where assets and database are subdirs of classroom_library_app,
        # and scripts are run from within classroom_library_app or its parent,
        # using "." or specific relative paths from the script's location is common.
        # Let's adjust to make it relative to the directory containing classroom_library_app
        # if run normally, or MEIPASS if bundled.
        # If main.py is classroom_library_app/main.py, then path for assets is assets/icon.png
        # and for database is database/library.db
        # These paths will be relative to sys._MEIPASS when bundled.
        # If not bundled, they are relative to where the script is run.
        # For consistency, let's make it relative to the script's own directory structure.

        # This assumes utils.py is in classroom_library_app/
        # So, the app's base for data (assets, database folders) is its own directory.
        base_path = os.path.abspath(".") # This will be classroom_library_app if script is run from there
                                        # Or the root of the project if run as classroom_library_app/main.py
                                        # For PyInstaller, paths like "assets/icon.png" are directly from _MEIPASS
                                        # For dev, if main.py is in classroom_library_app, then "assets/..." is correct.

        # A more robust way for development, assuming utils.py is in classroom_library_app/
        # and main.py is also in classroom_library_app/
        # and that classroom_library_app is the "application root" for relative paths.
        # When not bundled, if utils.py is at classroom_library_app/utils.py,
        # os.path.dirname(os.path.abspath(__file__)) is classroom_library_app/
        # This is the desired base_path for development if assets and database are subdirs of it.
        base_path = os.path.dirname(os.path.abspath(__file__)) # This gives classroom_library_app directory
        # However, the paths used in code are "assets/icons/..." and "database/library.db"
        # These are relative paths from where the main.py or db_setup.py are.
        # So, if main.py is classroom_library_app/main.py, it expects assets to be classroom_library_app/assets.
        # This is what `os.path.join(base_path_of_script_dir, relative_path)` would achieve.
        # The simplest is to rely on PyInstaller making these top-level in MEIPASS.
        # And for dev, that the current working directory is the project root,
        # and scripts are called like `python classroom_library_app/main.py`.
        # The provided --add-data maps `classroom_library_app/assets` to `assets` in bundle.
        # And `classroom_library_app/database` to `database` in bundle.
        # So, in bundled app, path is `assets/icon.png` and `database/library.db`.
        # In dev, if CWD is `classroom_library_app`, then `assets/icon.png` and `database/library.db` also work.
        # If CWD is project root, then `classroom_library_app/assets/icon.png` and `classroom_library_app/database/library.db`.

        # Let's use the most common PyInstaller pattern: relative paths from sys._MEIPASS or script's dir.
        # If script is in classroom_library_app, and assets/database are also in classroom_library_app,
        # then direct relative paths are fine.
        # The PyInstaller command maps classroom_library_app/assets -> assets (in bundle root)
        # and classroom_library_app/database -> database (in bundle root)
        # So the code should use "assets/..." and "database/..."

        # The most straightforward approach for PyInstaller when using --add-data src:dest
        # is that 'dest' becomes the path to use in code, relative to MEIPASS.
        # So, "assets/icons/icon.png" and "database/library.db" should work directly.
        # The helper is just to prepend sys._MEIPASS if bundled.
        base_path = getattr(sys, '_MEIPASS', os.path.abspath(".")) # PWD if not bundled, MEIPASS if bundled
                                                                # This might be problematic if PWD is not project root in dev.
                                                                # A better dev path: os.path.dirname(sys.argv[0]) or specific module's path

        # Given the project structure and typical execution:
        # classroom_library_app/main.py
        # classroom_library_app/utils.py
        # classroom_library_app/database/db_setup.py
        # classroom_library_app/assets/...
        # If run from project_root as `python classroom_library_app/main.py`:
        #   os.path.abspath(".") is project_root. Paths need to be "classroom_library_app/assets/..."
        # If run from classroom_library_app as `python main.py`:
        #   os.path.abspath(".") is classroom_library_app. Paths can be "assets/..."
        # sys._MEIPASS makes it simpler: it's always the root.

        # Let's assume the PyInstaller structure where 'assets' and 'database' are at the root of MEIPASS.
        # For development, this means scripts expect to be run from a context where 'assets' and 'database' are accessible.
        # Usually, this implies CWD is `classroom_library_app`.

        # A common robust pattern:
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # PyInstaller Bundle
            base_path = sys._MEIPASS
        else:
            # Development: path relative to the main script or a known project structure
            # Assuming main.py is in classroom_library_app and this util is also there.
            # We want paths relative to the "classroom_library_app" directory.
            base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
            # If sys.argv[0] is just "main.py", need to be careful.
            # A very common way if utils.py is in the project root or a known subfolder:
            # base_path = os.path.dirname(os.path.abspath(__file__)) # directory of utils.py
            # If utils.py is in classroom_library_app, this is classroom_library_app/.
            # Then, if assets is classroom_library_app/assets, path is os.path.join(base_path, "assets", filename)
            # But the PyInstaller command maps classroom_library_app/assets to just "assets" in the bundle.
            # So, the *relative_path* argument to this function should be "assets/icon.png".

            # Simplest for this structure, matching PyInstaller's mapping:
            # In dev, assume scripts are run from project root, and main is classroom_library_app/main.py
            # Then paths should be "classroom_library_app/assets/..."
            # Or, if running from classroom_library_app, then "assets/..."
            # The following assumes the latter for dev, and MEIPASS for bundle.
            # This means for dev, CWD should be classroom_library_app.
            base_path = os.path.abspath(".")


    return os.path.join(base_path, relative_path)

# Final refined version of get_data_path for this project structure:
# This function, if placed in utils.py within classroom_library_app,
# allows calling get_data_path("assets/icons/my_icon.png")
# or get_data_path("database/library.db")
# It correctly resolves for both bundled app and development (when run from project root OR classroom_library_app dir)

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running in a PyInstaller bundle
        base_path = sys._MEIPASS
        # The assets and database folders are copied to the root of MEIPASS
        # So, get_resource_path("assets/icons/my_icon.png") will correctly become MEIPASS/assets/icons/my_icon.png
    else:
        # Running in a normal Python environment
        # Assume this utils.py is in classroom_library_app/
        # The relative path is relative to the directory containing classroom_library_app/
        # No, it should be relative to classroom_library_app itself if main.py is there.
        # Let's make it relative to the project root (parent of classroom_library_app) for dev,
        # or relative to classroom_library_app if running from there.
        # This is tricky. The most consistent for dev matching the PyInstaller bundle structure is:
        # Assume the CWD is the `classroom_library_app` directory itself when running in dev.
        # Or, more robustly, make paths relative to the location of `main.py`.

        # If this utils.py is in classroom_library_app/
        # and main.py is in classroom_library_app/
        # and assets is in classroom_library_app/assets/
        # then from main.py, path to icon is "assets/icons/icon.png"
        # from utils.py, path to icon is also "assets/icons/icon.png" if CWD is classroom_library_app
        # This is the most straightforward interpretation matching PyInstaller's --add-data src:dest where dest is relative to MEIPASS root.
        base_path = os.path.abspath(".") # Assumes CWD is classroom_library_app in dev
                                      # Or, if main.py is the main entry point:
                                      # base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
                                      # This usually points to the directory of the script that was initially run.
                                      # If main.py is classroom_library_app/main.py, this is classroom_library_app/

        # Let's use a simpler, more direct approach for the PyInstaller bundle structure:
        # The paths "assets/..." and "database/..." are expected to be at the root of the bundle.
        # For development, this means these folders should be in the CWD when running main.py,
        # OR main.py is structured to find them relative to its own location.
        # The current code (e.g. "assets/icons/icon.png") assumes the CWD is `classroom_library_app`.
        # PyInstaller's mapping `--add-data classroom_library_app/assets:assets` makes this work in bundle.
        # So, the key is ensuring dev environment matches this or uses absolute paths derived from __file__.

        # Final proposed solution for get_resource_path:
        # This function will be in classroom_library_app/utils.py
        # It will construct paths relative to the 'classroom_library_app' directory in dev,
        # and relative to MEIPASS in bundle.
        # The paths passed to it should be like "assets/icons/my_icon.png" or "database/library.db"
        # These are treated as relative to the "application data root"

        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except AttributeError: # Using AttributeError for when _MEIPASS is not defined
            # Not running in a bundle, so use path relative to this utils.py file's directory
            # which is classroom_library_app/
            base_path = os.path.abspath(os.path.dirname(__file__))

        # The relative_path argument should be like "assets/icon.png" or "database/library.db"
        # if assets and database are at the same level as utils.py (i.e. inside classroom_library_app)
        # This is consistent with how PyInstaller is adding them.
        # However, the PyInstaller --add-data maps classroom_library_app/assets to 'assets' in bundle.
        # So, the path in code should just be 'assets/icon.png'.
        # And for database, 'database/library.db'.

        # Let's refine get_resource_path for clarity and correctness with the PyInstaller structure.
        # PyInstaller command implies:
        # classroom_library_app/assets/ -> assets/ in bundle
        # classroom_library_app/database/ -> database/ in bundle
        # So, the code should refer to "assets/..." and "database/..."
        # This function will prepend the MEIPASS path if bundled.
        # For dev, it assumes the script is run from a context where "assets" and "database" are accessible.
        # Usually, this means running `python main.py` from within the `classroom_library_app` directory.

        if hasattr(sys, '_MEIPASS'): # Running in PyInstaller bundle
            return os.path.join(sys._MEIPASS, relative_path)
        else: # Running in development
            # Path relative to the script being run (main.py)
            # Assumes main.py is in classroom_library_app/
            # and assets/database are subdirectories of classroom_library_app/
            # This makes "assets/..." and "database/..." directly usable from main.py's perspective.
            return os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), relative_path)
            # A small issue: if utils.py calls this for its own resources (not the case here), sys.argv[0] is still main.py
            # For this project, this should be fine as paths are for assets and db referenced from main context.

    # A simpler version that works if CWD is classroom_library_app for dev
    # and for PyInstaller due to how --add-data is used.
    # This is what the original prompt was leaning towards and is often sufficient.
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".") # CWD
    return os.path.join(base_path, relative_path)

# Let's stick to the last simple version, as it's most common with PyInstaller's data mapping.
# The key is that for development, the application must be run with `classroom_library_app` as the CWD.
# Example:
# cd classroom_library_app
# python main.py
# OR, if running from project root: python classroom_library_app/main.py
# In the latter case, os.path.abspath(".") is project_root.
# Then "assets/icons/icon.png" would resolve to "project_root/assets/icons/icon.png" which is wrong.
# It needs to be "project_root/classroom_library_app/assets/icons/icon.png".

# The most robust get_resource_path for this project:
# To be placed in classroom_library_app/utils.py
# This function, when called from anywhere within classroom_library_app (like main.py or db_setup.py),
# will correctly find paths like "assets/icon.png" or "database/library.db".
def get_true_resource_path(relative_path_from_app_root):
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller bundle: relative_path_from_app_root is directly under MEIPASS
        # because of how --add-data classroom_library_app/assets:assets is structured.
        # So, if relative_path_from_app_root is "assets/icon.png", it becomes MEIPASS/assets/icon.png
        return os.path.join(sys._MEIPASS, relative_path_from_app_root)
    else:
        # Development: Construct path relative to the 'classroom_library_app' directory.
        # utils.py is inside classroom_library_app. So, its parent is the project root.
        # The 'application root' for data files is the directory of utils.py.
        application_root_dir = os.path.dirname(os.path.abspath(__file__)) # This is classroom_library_app/
        return os.path.join(application_root_dir, relative_path_from_app_root)

# This 'get_true_resource_path' seems the most correct for the described structure and PyInstaller command.
# It assumes 'assets' and 'database' are subdirectories of where utils.py itself resides (i.e., classroom_library_app/).
# And the PyInstaller command correctly maps classroom_library_app/assets to 'assets' in bundle root.
# So, if we pass "assets/icon.png", in dev it becomes classroom_library_app/assets/icon.png
# In bundle, it becomes MEIPASS/assets/icon.png. This is consistent.

# Let's rename it to get_data_path as per the plan.
def get_data_path(relative_path_to_app_subfolder):
    """
    Get absolute path to a resource (e.g., "assets/icon.png", "database/library.db").
    Works for both development and PyInstaller bundle.
    Assumes this utils.py file is located in the main application directory
    (e.g., classroom_library_app/), and the relative_path_to_app_subfolder
    is relative to this directory.
    """
    if hasattr(sys, '_MEIPASS'):
        # Running in a PyInstaller bundle.
        # The --add-data maps like "classroom_library_app/assets:assets",
        # so "assets" is at the root of _MEIPASS.
        return os.path.join(sys._MEIPASS, relative_path_to_app_subfolder)
    else:
        # Running in a normal Python environment.
        # Get the directory of this utils.py file (e.g., .../classroom_library_app/)
        base_app_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_app_dir, relative_path_to_app_subfolder)

if __name__ == '__main__':
    # Test the function (assuming utils.py is in classroom_library_app)
    print(f"Path to assets/ (dev): {get_data_path('assets')}")
    print(f"Path to database/library.db (dev): {get_data_path('database/library.db')}")
    # To test bundled path, you'd set sys._MEIPASS temporarily (for test only)
    # class MockSys: _MEIPASS = "/TEMP_BUNDLE_PATH"
    # original_sys = sys
    # sys = MockSys()
    # print(f"Path to assets/ (bundle): {get_data_path('assets')}")
    # sys = original_sys # restore
