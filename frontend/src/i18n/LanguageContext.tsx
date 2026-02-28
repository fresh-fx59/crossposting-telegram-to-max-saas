import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import en, { type Translations } from './en';
import ru from './ru';
import { getStoredValue, setStoredValue } from '../services/storage';

export type Language = 'ru' | 'en';

const translations: Record<Language, Translations> = { en, ru };

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: Translations;
}

const LanguageContext = createContext<LanguageContextType>({
  language: 'ru',
  setLanguage: () => {},
  t: ru,
});

function getInitialLanguage(): Language {
  const stored = getStoredValue('language');
  if (stored === 'en' || stored === 'ru') return stored;

  // Detect from browser settings
  const browserLang = navigator.language || (navigator as any).userLanguage || '';
  if (browserLang.startsWith('en')) return 'en';

  // Default to Russian
  return 'ru';
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>(getInitialLanguage);

  const setLanguage = useCallback((lang: Language) => {
    setLanguageState(lang);
    setStoredValue('language', lang);
    document.documentElement.lang = lang;
  }, []);

  // Set initial html lang attribute
  document.documentElement.lang = language;

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t: translations[language] }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  return useContext(LanguageContext);
}
