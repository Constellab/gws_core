<p align="center">
  <img src="https://constellab.space/assets/fl-logo/constellab-logo-text-white.svg" alt="Constellab Logo" width="80%">
</p>

<br/>

# 👋 Welcome to GWS Core 

```gws_core``` is a [Constellab](https://constellab.io) library (called bricks) developped by [Gencovery](https://gencovery.com/). GWS stands for Gencovery Web Services.

## 🚀 What is Constellab?


✨ [Gencovery](https://gencovery.com/) is a software company that offers [Constellab](https://constellab.io), the leading open and secure digital infrastructure designed to consolidate data and unlock its full potential in the life sciences industry. Gencovery's mission is to provide universal access to data to enhance people's health and well-being.

🌍 With our Fair Open Access offer, you can use Constellab for free. [Sign up here](https://constellab.space/). Find more information about the Open Access offer here (link to be defined).


## ✅ Features

⚠️ **This brick is required to run the data lab.** ⚠️

This repository is the core library for Constellab data lab. It provides the achitecture and API for the data lab. It also provides all the feature to develop new bricks.
 
📋 Here is the list of the main features:
- Running the data lab's API.
- Setting up the data lab's architecture.
- Managing pipelines and data.
- Providing classes for data and database manipulation.

It also include standard ```Resources``` (like Table, File, Folder, PlotlyResource, Note resource...) and ```Tasks``` (for manipulating theses resources). You can find the list of theses ```Resources``` and ```Tasks``` in the ```gws_core``` documentation.

## 📄 Documentation

📄  For `gws_core` brick documentation, click [here](https://constellab.community/bricks/gws_core/latest/doc/getting-started/6efb7ab9-8508-4f99-b3e1-1a43e55755c4)

💫 For Constellab application documentation, click [here](https://constellab.community/bricks/gws_academy/latest/doc/getting-started/b38e4929-2e4f-469c-b47b-f9921a3d4c74)

## 🛠️ Installation

### 🔥 Recommended Method

The best way to install a brick is through the Constellab platform. With our Fair Open Access offer, you get a free cloud data lab where you can install bricks directly. [Sign up here](https://constellab.space/)

Learn about the data lab here : [Overview](https://constellab.community/bricks/gws_academy/latest/doc/digital-lab/overview/294e86b4-ce9a-4c56-b34e-61c9a9a8260d) and [Data lab management](https://constellab.community/bricks/gws_academy/latest/doc/digital-lab/on-cloud-digital-lab-management/4ab03b1f-a96d-4d7a-a733-ad1edf4fb53c)

### 🔧 Manual installation

This section is for users who want to install the brick manually. It can also be used to install the brick manually in the Constellab Codelab.

We recommend installing using Ubuntu 22.04 with python 3.10.

Required packages are listed in the ```settings.json``` file, for now the packages must be installed manually.

```bash 
pip install openpyxl==3.1.4 awesome-slugify==1.6.5 fastapi==0.111.0 pydantic==2.7.4 peewee==3.17.5 psutil==5.9.8 pyjwt==2.8.0 pymysql==1.1.1 python-multipart==0.0.9 starlette-context==0.3.6 uvicorn==0.30.1 charset-normalizer==2.1.1 dill==0.3.8 numpy==1.26.4 pandas==2.2.2 matplotlib==3.9.0 scipy==1.13.1 scikit-learn==1.5.0 openai==1.60.2 typing_extensions==4.12.2 boto3==1.34.127 "boto3-stubs[s3]==1.34.127" plotly==5.22.0 simplejson==3.19.2 xmltodict==0.13.0 streamlit==1.42.2 beautifulsoup4==4.12.3 grpcio==1.64.1 schedule==1.2.2
```

#### Usage


▶️ To start the server :

```bash
gws server run
```

🕵️ To run a given unit test

```bash
gws server test [TEST_FILE_NAME]
```

Replace `[TEST_FILE_NAME]` with the name of the test file (without `.py`) in the tests folder. Execute this command in the folder of the brick.

🕵️ To run the whole test suite, use the following command:

```bash
gws server test all
```

📌 VSCode users can use the predefined run configuration in `.vscode/launch.json`.

## 🤗 Community

🌍 Join the Constellab community [here](https://constellab.community/) to share and explore stories, code snippets and bricks with other users.

🚩 Feel free to open an issue if you have any question or suggestion.

☎️ If you have any questions or suggestions, please feel free to contact us through our website: [Constellab](https://constellab.io/).

## 🌎 License

```gws_core``` is completely free and open-source and licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html).

<br/>


This brick is maintained with ❤️ by [Gencovery](https://gencovery.com/).

<p align="center">
  <img src="https://framerusercontent.com/images/Z4C5QHyqu5dmwnH32UEV2DoAEEo.png?scale-down-to=512" alt="Gencovery Logo"  width="30%">
</p>