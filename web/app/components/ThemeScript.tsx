/**
 * Pre-hydration inline script to apply the stored theme before paint,
 * avoiding a light/dark flash on first render. Renders no DOM.
 */
export default function ThemeScript() {
  const js = `(function(){try{var t=localStorage.getItem('wucg-theme');if(t==='light'||t==='dark'){document.documentElement.setAttribute('data-theme',t);}}catch(e){}})();`;
  return <script dangerouslySetInnerHTML={{ __html: js }} />;
}
