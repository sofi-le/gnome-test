import React, { useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, Image,
  SafeAreaView, StatusBar, Alert, Animated, Dimensions, ActivityIndicator,
} from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import { useFonts, PlayfairDisplay_700Bold } from '@expo-google-fonts/playfair-display';
import { parseFile } from './lib/api';
import { useApp } from './lib/AppContext';

const C = {
  bg:            '#F7F6F2',
  surface:       '#FFFFFF',
  textPrimary:   '#1A1B14',
  textSecondary: '#686760',
  textLight:     '#A1A199',
  green:         '#44A353',
  olive:         '#363E28',
  lightOlive:    '#DAE4CF',
  lightGreen:    '#EEF2E9',
};

const { width: SCREEN_W } = Dimensions.get('window');

const ACCEPTED_TYPES = ['text/plain', 'text/csv', 'application/zip', 'application/x-zip-compressed', '*/*'];

interface Props {
  onFileSelected: () => void;
}

export default function UploadScreen({ onFileSelected }: Props) {
  const { setParseResult, setError } = useApp();
  const [pickedFileName, setPickedFileName] = useState<string | null>(null);
  const [parsing, setParsing]               = useState(false);
  const [errorMsg, setErrorMsg]             = useState<string | null>(null);
  const [buttonScale]                       = useState(new Animated.Value(1));
  const [fontsLoaded]                       = useFonts({ PlayfairDisplay_700Bold });

  const handleChooseFile = useCallback(async () => {
    Animated.sequence([
      Animated.timing(buttonScale, { toValue: 0.96, duration: 80, useNativeDriver: true }),
      Animated.timing(buttonScale, { toValue: 1,    duration: 80, useNativeDriver: true }),
    ]).start();

    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ACCEPTED_TYPES,
        copyToCacheDirectory: true,
        multiple: false,
      });

      if (result.canceled) return;
      const asset = result.assets[0];

      const ext = asset.name.split('.').pop()?.toLowerCase();
      if (!['txt', 'csv', 'zip'].includes(ext ?? '')) {
        Alert.alert('Unsupported file', 'Please upload a TXT, CSV, or ZIP file from 23andMe or AncestryDNA.');
        return;
      }

      setPickedFileName(asset.name);
      setParsing(true);
      setErrorMsg(null);

      console.log(`[Upload] picked file: ${asset.name}  uri: ${asset.uri}`);

      try {
        const parsed = await parseFile(asset.uri, asset.name, (asset as any).file ?? undefined);
        console.log('[Upload] parse success:', parsed);
        setParseResult(parsed);
        setTimeout(onFileSelected, 300);
      } catch (err: any) {
        console.error('[Upload] parse error:', err);
        setParsing(false);
        const msg: string = err?.message ?? 'Unknown error';
        setErrorMsg(msg);
        Alert.alert('Upload failed', msg);
      }
    } catch {
      Alert.alert('Error', 'Could not open file picker. Please try again.');
    }
  }, [buttonScale, onFileSelected]);

  const handleWhatIsThis = useCallback(() => {
    Alert.alert(
      'About G-Nome',
      'G-Nome turns your raw DNA data file into a personalised genomic health passport.\n\nWe support exports from 23andMe and AncestryDNA. Your file stays private — processing happens locally in the app.',
      [{ text: 'Got it' }],
    );
  }, []);

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar barStyle="dark-content" backgroundColor={C.bg} />

      <View style={styles.logoArea}>
        <Text style={[styles.logoText, fontsLoaded && styles.logoTextFont]}>G-Nome</Text>
        <Text style={styles.tagline}>Your genome. Your story.{'\n'}Your Legacy</Text>
      </View>

      <Image
        source={require('./assets/images/gnome_img.png')}
        style={styles.gnomeImage}
        resizeMode="contain"
      />

      <View style={styles.card}>
        <View style={styles.iconWrapper}>
          <View style={styles.iconBg}>
            <View style={styles.arrowShaft} />
            <View style={styles.arrowHeadLeft} />
            <View style={styles.arrowHeadRight} />
          </View>
        </View>

        <Text style={styles.uploadTitle}>Upload your DNA file</Text>
        <Text style={styles.uploadSubtitle}>23andMe or AncestryDNA</Text>
        <Text style={styles.fileTypes}>TXT  ·  CSV  ·  ZIP</Text>

        {pickedFileName && (
          <View style={[styles.selectedFileRow, errorMsg ? styles.selectedFileRowError : null]}>
            {parsing ? (
              <ActivityIndicator size="small" color={C.green} />
            ) : errorMsg ? (
              <Text style={styles.errorDot}>✕</Text>
            ) : (
              <View style={styles.checkCircle}>
                <Text style={styles.checkMark}>✓</Text>
              </View>
            )}
            <Text style={[styles.selectedFileName, errorMsg ? { color: '#C73838' } : null]} numberOfLines={1}>
              {parsing ? `Parsing ${pickedFileName}…` : pickedFileName}
            </Text>
          </View>
        )}

        {errorMsg && (
          <View style={styles.errorBanner}>
            <Text style={styles.errorText} numberOfLines={5}>{errorMsg}</Text>
          </View>
        )}

        <Animated.View style={{ transform: [{ scale: buttonScale }], width: '100%' }}>
          <TouchableOpacity
            style={[styles.chooseButton, pickedFileName && !parsing && styles.chooseButtonDone]}
            onPress={handleChooseFile}
            activeOpacity={0.85}
            disabled={parsing}
          >
            {parsing ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.chooseButtonText}>
                {pickedFileName ? 'Change File' : 'Choose File'}
              </Text>
            )}
          </TouchableOpacity>
        </Animated.View>

        <TouchableOpacity onPress={handleWhatIsThis} hitSlop={{ top: 12, bottom: 12, left: 20, right: 20 }}>
          <Text style={styles.whatIsThis}>What is this?</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.bg, alignItems: 'center' },

  logoArea: { alignItems: 'center', marginTop: 16 },
  logoText: { fontSize: 38, fontWeight: '700', color: C.olive },
  logoTextFont: { fontFamily: 'PlayfairDisplay_700Bold' },
  tagline: { fontSize: 14, color: C.textSecondary, textAlign: 'center', lineHeight: 20, marginTop: 2, fontStyle: 'italic' },

  gnomeImage: { width: SCREEN_W * 0.65, height: 238, marginTop: 6 },

  card: {
    width: SCREEN_W - 40,
    backgroundColor: C.surface,
    borderRadius: 16,
    marginTop: 10,
    paddingHorizontal: 24,
    paddingTop: 24,
    paddingBottom: 28,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 16,
    elevation: 6,
  },

  iconWrapper: { marginBottom: 14 },
  iconBg: {
    width: 44, height: 44, borderRadius: 22,
    backgroundColor: C.lightOlive,
    alignItems: 'center', justifyContent: 'center',
  },
  arrowShaft: {
    position: 'absolute', width: 2.5, height: 14,
    backgroundColor: C.green, borderRadius: 2, bottom: 13,
  },
  arrowHeadLeft: {
    position: 'absolute', width: 7, height: 2.5,
    backgroundColor: C.green, borderRadius: 2,
    top: 12, left: 11, transform: [{ rotate: '-45deg' }],
  },
  arrowHeadRight: {
    position: 'absolute', width: 7, height: 2.5,
    backgroundColor: C.green, borderRadius: 2,
    top: 12, right: 11, transform: [{ rotate: '45deg' }],
  },

  uploadTitle: { fontSize: 14, fontWeight: '600', color: C.textPrimary, textAlign: 'center' },
  uploadSubtitle: { fontSize: 11, color: C.textSecondary, textAlign: 'center', marginTop: 6 },
  fileTypes: { fontSize: 10, color: C.textLight, textAlign: 'center', marginTop: 4, letterSpacing: 1 },

  selectedFileRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: C.lightGreen,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginTop: 14,
    width: '100%',
    gap: 10,
  },
  selectedFileRowError: {
    backgroundColor: '#FEF1F1',
  },
  errorDot: {
    fontSize: 13,
    color: '#C73838',
    fontWeight: '700',
    width: 24,
    textAlign: 'center',
  },
  errorBanner: {
    backgroundColor: '#FEF1F1',
    borderRadius: 8,
    borderLeftWidth: 3,
    borderLeftColor: '#C73838',
    padding: 10,
    marginTop: 8,
    width: '100%',
  },
  errorText: {
    fontSize: 10,
    color: '#C73838',
    lineHeight: 15,
  },
  checkCircle: {
    width: 24, height: 24, borderRadius: 12,
    backgroundColor: C.green, alignItems: 'center', justifyContent: 'center',
  },
  checkMark: { color: '#fff', fontSize: 12, fontWeight: '700' },
  selectedFileName: { fontSize: 12, fontWeight: '600', color: C.textPrimary, flex: 1 },

  chooseButton: {
    width: '100%', height: 46, backgroundColor: C.olive,
    borderRadius: 12, alignItems: 'center', justifyContent: 'center', marginTop: 18,
    shadowColor: '#000', shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.10, shadowRadius: 10, elevation: 4,
  },
  chooseButtonDone: { backgroundColor: C.green },
  chooseButtonText: { fontSize: 14, fontWeight: '600', color: '#FFFFFF' },

  whatIsThis: { fontSize: 11, color: C.green, marginTop: 16 },
});
