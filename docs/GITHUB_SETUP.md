# Putting the project on GitHub and running the live demo

## One time (PowerShell, from the folder that holds the unzipped project)
```
git init
git add .
git commit -m "SAOS digital twin v0.21"
git branch -M main
git remote add origin https://github.com/<your-user>/saos-digital-twin.git
git push -u origin main
```
Create the empty repository on github.com first (no README). `arduino/esp32_gateway/wifi_secrets.h` is git-ignored; never commit real Wi-Fi passwords or API keys.

## Update later (zip workflow)
Unzip a new `saos_sim.zip` over the repo folder: `Expand-Archive -Force -Path "$env:USERPROFILE\Downloads\saos_sim.zip" -DestinationPath .`, then `git add -A`, `git commit -m "..."`, `git push`.

## Run the demo on your PC
```
pip install -r requirements.txt
streamlit run app.py
```
## Put the demo online (free)
On share.streamlit.io choose "New app", pick the repository, branch `main`, main file `app.py`. Every push to GitHub updates it.
GitHub Actions (`.github/workflows/ci.yml`) runs the C++ checks and the Python tests on each push; a red cross means something broke.
