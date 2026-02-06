# Character Audio Assets

This directory contains character-specific audio files for the manga animation pipeline.

## Directory Structure

```
characters/
├── {character_name}/
│   ├── attacks/          # Named attack sound effects
│   │   └── {attack_name}.wav
│   └── personality/      # Character vocalizations
│       └── {cue_type}.wav
```

## Naming Conventions

**Character Names:** `lowercase` (e.g., `luffy`, `zoro`, `sanji`)

**Attack Files:** `snake_case` (e.g., `gum_gum_pistol.wav`, `asura_bakki.wav`)

**Personality Files:** `snake_case` (e.g., `laugh.wav`, `super.wav`, `yohohoho.wav`)

## Supported Formats

- **WAV** (preferred) - 44100 Hz, stereo
- **MP3** (fallback)

## Example Characters

### Luffy
- **Attacks:** `gum_gum_pistol.wav`, `gum_gum_gatling.wav`
- **Personality:** `laugh.wav`, `hehe.wav`

### Zoro
- **Attacks:** `asura_bakki.wav`
- **Personality:** `hmph.wav`

### Sanji
- **Attacks:** `sky_walk.wav`
- **Personality:** `hello_ladies.wav`

### Nami
- **Attacks:** `lightning_thunder.wav`
- **Personality:** `angry.wav`

### Usopp
- **Attacks:** `bamboo_blast.wav`
- **Personality:** `panic.wav`

### Franky
- **Personality:** `super.wav`

### Brook
- **Personality:** `yohohoho.wav`

## Adding New Characters

1. Create character directory: `assets/characters/{character_name}/`
2. Create subdirectories: `attacks/` and/or `personality/`
3. Add audio files with snake_case names
4. No code changes required - system auto-discovers

## Audio Resolution

The system automatically resolves audio files based on Gemini's intent output:

```json
{
  "attack": {
    "character": "luffy",
    "name": "gum_gum_pistol"
  }
}
```

Resolves to: `assets/characters/luffy/attacks/gum_gum_pistol.wav`

## Fallback Behavior

- **Missing attack audio** → Uses generic impact SFX
- **Missing personality audio** → Skips silently
- **Unknown character** → Skips silently

No crashes, graceful degradation.
