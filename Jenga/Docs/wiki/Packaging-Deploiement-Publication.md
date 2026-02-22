# Packaging, Déploiement, Publication

Cette page couvre les commandes opérationnelles:

- `jenga package`
- `jenga deploy`
- `jenga publish`
- `jenga sign`
- `jenga keygen`

## Packaging

### Android APK

```bash
jenga package --platform android --type apk --project MonApp --config Release
```

### iOS IPA

```bash
jenga package --platform ios --type ipa --project MonApp --config Release
```

### Windows ZIP

```bash
jenga package --platform windows --type zip --project MonApp --output ./dist
```

## Signature Android

### Générer une keystore

```bash
jenga keygen --interactive
```

### Signer un APK

```bash
jenga sign --apk ./Build/Bin/Debug/MonApp/MonApp.apk \
           --keystore ./keystore.jks \
           --alias mykey \
           --storepass xxxx \
           --keypass xxxx
```

## Déploiement

### Android (adb)

```bash
jenga deploy --platform android --project MonApp
```

### iOS

```bash
jenga deploy --platform ios --project MonApp
```

## Publication

```bash
jenga publish --registry nuget --package ./dist/MonPackage.nupkg --api-key <TOKEN>
```

## Limitations actuelles (code actuel)

- `publish`: seul le flux NuGet est réellement implémenté; le reste est partiel.
- `deploy`: Linux n'est pas encore implémenté.
- `profile`: certaines plateformes sont encore en mode placeholder.
