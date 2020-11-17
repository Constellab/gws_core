window.addEventListener("load", function () {
    const drawer = mdc.drawer.MDCDrawer.attachTo(document.querySelector('.mdc-drawer'));
    const progressBar = mdc.linearProgress.MDCLinearProgress.attachTo(document.querySelector('.mdc-linear-progress'));
    progressBar.open()

    const listEl = document.querySelector('.mdc-drawer .mdc-list');
    const mainContentEl = document.querySelector('.main-content');

    listEl.addEventListener('click', (event) => {
        drawer.open = false;
    });

    document.body.addEventListener('MDCDrawer:closed', () => {
        //mainContentEl.querySelector('input, button').focus();
    });

    const btn = document.querySelector('.mdc-top-app-bar--short');
    btn.addEventListener('click', (event) => {
        drawer.open = true;
    });
    
    GView.upgradeAll()
    progressBar.close()
})