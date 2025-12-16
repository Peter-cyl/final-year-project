# Setting Up the XAIP Framework on Ubuntu

This guide helps you complete the first supervisor task:
> "Complete the C++ XAIP Framework compilation and successfully run the provided demo"

---

## Prerequisites

- Ubuntu 18.04 or higher (use VirtualBox VM if on Mac/Windows)
- cmake
- Boost library
- Qt5

---

## Step 1: Install Dependencies

Open a terminal and run:

```bash
# Update package list
sudo apt-get update

# Install cmake
sudo apt-get install cmake

# Install Boost
sudo apt-get install libboost-all-dev

# Install Qt5 (for Ubuntu 22.04)
sudo apt-get install qtbase5-dev qtchooser qt5-qmake qtbase5-dev-tools
sudo apt-get install qtcreator
```

For Qt5 on different Ubuntu versions, see:
https://askubuntu.com/questions/1404263/how-do-you-install-qt-on-ubuntu22-04

---

## Step 2: Get the XAIPFramework

Download from the Google Drive link your supervisor provided:
```
https://drive.google.com/drive/folders/182LGq026xskfx4cYo4279Ngp2vVG0TC
```

Or if you have it locally, copy it to Ubuntu.

---

## Step 3: Compile the Framework

```bash
# Navigate to the XAIPFramework directory
cd XAIPFramework

# Create build directory
mkdir build

# Enter build directory
cd build

# Generate makefiles
cmake ..

# Compile
make

# Run the application
./appui
```

---

## Step 4: Run the Demo

1. **Start the app:**
   ```bash
   ./appui
   ```

2. **Load domain and problem files:**
   - Domain and problem files should be in `XAIPFramework/common/`
   - There's already one domain in there

3. **Follow these steps in the UI:**
   - Load the domain file
   - Load the problem file  
   - Give a plan name in "plan name" field
   - Click "Save"
   - Click "Continue"
   - Select plan
   - Click "Continue"
   - Try some questions
   - Select different highlights

---

## Troubleshooting

### "cmake .." fails
- Make sure you're in the `build` directory inside `XAIPFramework`
- Check that cmake is installed: `cmake --version`

### "make" fails with Qt errors
- Verify Qt5 is installed: `qmake --version`
- Try: `sudo apt-get install qt5-default` (older Ubuntu)

### Application crashes
- Check that domain/problem files are in `common/` folder
- Make sure files have correct PDDL syntax

### Can't find VAL (validator)
- The framework uses VAL for plan validation
- It may be included in `planners/` directory
- Or install separately from: https://nms.kcl.ac.uk/planning/software/val.html

---

## What to Note for Your Project

When you run the framework and ask questions, observe:

1. **What format does the abstraction output use?**
   - This is what your Python code needs to parse
   - Example: `predicate-refrigeratedttruck`

2. **Where are output files saved?**
   - Usually in `XAIPFramework/common/`
   - Look for `hplan.pddl`, `xdomain.pddl`, etc.

3. **What information is displayed in the UI?**
   - This tells you what your NLG system needs to verbalize

---

## Code Locations (for reference)

- **Backend compilation logic:** `src/compilator/`
- **UI code:** `src/human_interface/`
- **Question handling:** `src/structures/question/`
- **PDDL parsing:** `src/model_interface/`

---

## After Setup is Complete

Once you have the framework running:

1. Take screenshots of the UI for your report
2. Note the exact format of abstraction outputs
3. Test with the refrigeration domain
4. Connect your Python verbalizer to process the outputs

---

## Quick Test Checklist

- [ ] Ubuntu VM or native Ubuntu set up
- [ ] cmake installed
- [ ] Boost installed  
- [ ] Qt5 installed
- [ ] XAIPFramework downloaded
- [ ] `cmake ..` runs without errors
- [ ] `make` compiles successfully
- [ ] `./appui` launches the GUI
- [ ] Can load domain/problem files
- [ ] Can generate a plan
- [ ] Can ask a question and see results
