<template>
  <v-app class="app-shell">
    <div class="app-shell__bg" />
    <v-main class="app-shell__main">
      <router-view />
    </v-main>
  </v-app>
</template>

<style>
.app-shell {
  background: transparent !important;
}

.app-shell__bg {
  background:
    radial-gradient(ellipse 80% 60% at 10% 0%, rgba(74, 173, 111, 0.1), transparent 55%),
    radial-gradient(ellipse 70% 50% at 90% 10%, rgba(232, 145, 58, 0.1), transparent 50%),
    radial-gradient(ellipse 60% 40% at 50% 100%, rgba(52, 211, 153, 0.06), transparent 55%),
    linear-gradient(180deg, #0a0e17 0%, #0f172a 50%, #0a0e17 100%);
  inset: 0;
  pointer-events: none;
  position: fixed;
  z-index: 0;
}

.app-shell__main {
  position: relative;
  z-index: 1;
}
</style>
