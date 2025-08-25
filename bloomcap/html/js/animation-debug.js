/* ===================================================================
   ANIMATION DEBUG - Tests en temps réel
   =================================================================== */

// Test immédiat au chargement
document.addEventListener('DOMContentLoaded', () => {
  console.log('🔍 DIAGNOSTIC ANIMATIONS');
  
  // Vérifier les fichiers CSS
  const modernAnimCSS = Array.from(document.styleSheets).find(sheet => 
    sheet.href && sheet.href.includes('modern-animations.css')
  );
  console.log('CSS moderne chargé:', modernAnimCSS ? '✅' : '❌');
  
  // Vérifier les éléments avec classes
  const animElements = document.querySelectorAll('.animate-on-scroll');
  console.log(`Éléments trouvés: ${animElements.length}`);
  
  animElements.forEach((el, i) => {
    console.log(`Élément ${i+1}:`, el.className);
  });
  
  // Test manuel - animer immédiatement tous les éléments
  window.testAnimations = () => {
    console.log('🧪 TEST MANUEL - Animation forcée');
    animElements.forEach((el, i) => {
      setTimeout(() => {
        el.classList.add('is-visible');
        console.log(`Élément ${i+1} animé`);
      }, i * 200);
    });
  };
  
  // Auto-test après 2 secondes
  setTimeout(() => {
    if (animElements.length > 0) {
      console.log('🚀 AUTO-TEST démarré');
      window.testAnimations();
    }
  }, 2000);
  
  console.log('💡 Tapez testAnimations() dans la console pour test manuel');
});