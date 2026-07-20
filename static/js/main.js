// إخفاء عنصر شاشة الافتتاح فعلياً من DOM بعد انتهاء الأنيميشن (وليس فقط opacity:0)
// حتى لا يعيق أي تفاعل مع الصفحة بعدها.
document.addEventListener('DOMContentLoaded', () => {
  const splash = document.getElementById('splash');
  if (splash) {
    setTimeout(() => {
      splash.remove();
      document.body.classList.remove('has-splash');
    }, 3400);
  }

  // إخفاء تلقائي لرسائل التنبيه (Toasts) بعد فترة
  document.querySelectorAll('.toast').forEach((toast, i) => {
    setTimeout(() => {
      toast.style.transition = 'opacity .4s ease, transform .4s ease';
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(-10px)';
      setTimeout(() => toast.remove(), 400);
    }, 6000 + i * 300);
  });
});
