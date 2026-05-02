# Subtitor Local

<p align="center">
  <img src="subtitorlocalLOGO.png" width="180" alt="Subtitor Local Logo"/>
</p>

<p align="center">
  Sous-titres animés style CapCut, 100% local, sans abonnement, propulsé par WhisperX.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python" />
  <img src="https://img.shields.io/badge/WhisperX-transcription-green?style=flat-square" />
  <img src="https://img.shields.io/badge/GPU-CUDA%20%7C%20CPU-orange?style=flat-square" />
  <img src="https://img.shields.io/badge/OS-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey?style=flat-square" />
  <img src="https://img.shields.io/badge/licence-MIT-purple?style=flat-square" />
</p>

---

## ✨ Fonctionnalités

| Fonctionnalité | Détail |
|---|---|
| 🎙 Transcription automatique | WhisperX avec alignement forcé — timestamps précis mot par mot |
| 🎬 Preview intégrée | Player vidéo dans l'app avec son synchronisé |
| ✏️ Éditeur de sous-titres | Correction manuelle des mots et timestamps |
| 🎨 Styles avancés | Taille, couleur, contour, ombre, fond de mot, karaoké |
| ✨ Effet karaoké | Les mots se surlignent un à un en temps réel |
| 🔢 N mots par affichage | 1 à 8 mots affichés simultanément, configurable |
| 🌈 Effets couleur | Fixe, gradient animé, négatif dynamique |
| 🎬 Animations | Pop, fade, slide up/down, bounce |
| 🖥 Green screen / Black screen | Export sans la vidéo, fond vert ou noir |
| 📄 Export SRT | Compatible avec tous les lecteurs vidéo |
| 💾 Export MP4 | Sous-titres incrustés, audio conservé |
| 🔤 Police personnalisée | Import de fichiers `.ttf` / `.otf` |
| ⚡ GPU / CPU | Détection automatique — CUDA si dispo, CPU sinon |

---

## 🎨 Presets inclus

| Preset | Style |
|---|---|
| **TikTok Neon** | Contour magenta, glow, animation bounce |
| **CapCut Glow** | Fond sombre arrondi, halo bleu, animation pop |
| **Minimal White** | Propre et lisible, fade discret |
| **Bold & Yellow** | Jaune vif, gros texte, 2 mots à la fois |
| **Retro VHS** | Cyan + rose, look années 80 |

---

## 📦 Téléchargement

Les binaires sont disponibles dans l'onglet **[Actions](../../actions)** → dernier build → **Artifacts**.

| Plateforme | Version | Fichier |
|---|---|---|
| Windows | CPU | `Subtitor-Windows-CPU.zip` |
| Windows | GPU (Nvidia) | `Subtitor-Windows-GPU.zip` |
| Linux | CPU | `Subtitor-Linux-CPU-deb.zip` |
| Linux | GPU (Nvidia) | `Subtitor-Linux-GPU-deb.zip` |
| macOS | CPU | `Subtitor-macOS.zip` |

> **Linux** : installe avec `sudo dpkg -i Subtitor-CPU.deb`  
> **macOS** : ouvre le `.dmg` et glisse dans Applications  
> **Windows** : double-clic sur le `.exe`, aucune installation requise

---

## 🚀 Installation depuis les sources

### Prérequis système

```bash
# Ubuntu / Debian
sudo apt install python3 python3-pip python3-venv ffmpeg

# macOS
brew install python ffmpeg

# Windows
# Installe Python depuis python.org et FFmpeg depuis ffmpeg.org
```

### Installation

```bash
git clone https://github.com/nopy234536758/subtitor.git
cd subtitor
python3 -m venv env
source env/bin/activate  # Windows : env\Scripts\activate
```

**CPU only (recommandé si pas de GPU Nvidia) :**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

**GPU Nvidia (CUDA) :**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**Puis les dépendances :**
```bash
pip install whisperx customtkinter opencv-python numpy Pillow moviepy pygame
```

### Lancement

```bash
python subtitor_local.py
```

---

## 🖥 Utilisation

### 1. Charger une vidéo
Clique sur **📂 Charger une vidéo** et sélectionne ton fichier (`.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`).

### 2. Transcrire
Choisis le modèle Whisper selon tes besoins :

| Modèle | Vitesse | Qualité | RAM |
|---|---|---|---|
| `tiny` | ⚡⚡⚡⚡ | ⭐⭐ | ~1 Go |
| `small` | ⚡⚡⚡ | ⭐⭐⭐ | ~2 Go |
| `medium` | ⚡⚡ | ⭐⭐⭐⭐ | ~5 Go |
| `large` | ⚡ | ⭐⭐⭐⭐⭐ | ~10 Go |

> `small` est recommandé pour un bon compromis vitesse/qualité sur CPU.

Clique sur **🎙 Transcrire** et attends la fin du traitement.

### 3. Corriger les sous-titres (optionnel)
L'éditeur affiche les mots avec leurs timestamps. Tu peux les modifier manuellement puis cliquer **Appliquer ✓**.

### 4. Personnaliser le style
Le panneau de droite permet de régler :
- **Affichage** : nombre de mots par bloc (1 à 8)
- **Texte** : taille, couleur, gras, italique, majuscules
- **Contour** : épaisseur, couleur
- **Ombre** : activation, couleur, opacité, décalage, flou
- **Fond du mot** : activation, couleur, opacité, padding, arrondi
- **Karaoké** : couleur du mot actif, couleur des mots passés
- **Position** : Y, X, alignement
- **Animation** : pop / fade / slide / bounce + durée
- **Couleur** : fixe / gradient / négatif dynamique
- **Police** : import `.ttf` / `.otf`

### 5. Exporter
- **💾 Exporter MP4** : vidéo finale avec sous-titres incrustés
- **📄 Exporter SRT** : fichier de sous-titres compatible partout
- **👁 Preview rapide** : export des 45 premières secondes pour vérifier

---

## 🎬 Modes de fond

| Mode | Résultat |
|---|---|
| **Vidéo** | Sous-titres par-dessus la vidéo originale |
| **Green screen** | Fond vert uni — pour chroma key dans un logiciel de montage |
| **Black screen** | Fond noir uni — pour incrustation |

---

## 🔧 Configuration requise

| | Minimum | Recommandé |
|---|---|---|
| OS | Windows 10 / Ubuntu 20.04 / macOS 12 | Windows 11 / Ubuntu 22.04 / macOS 14 |
| CPU | 4 cœurs | 8 cœurs |
| RAM | 8 Go | 16 Go |
| GPU | — | Nvidia avec 4 Go VRAM (CUDA) |
| Espace disque | 5 Go | 10 Go |

---

## 📄 Licence

MIT — libre pour usage personnel et commercial.
