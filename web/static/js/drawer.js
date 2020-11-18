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

    const sidebarBtn = document.querySelector('.gws-top-bar--open-sidebar-btn');
    sidebarBtn.addEventListener('click', (event) => {
        drawer.open = true;
    });
    
    const menu = mdc.menu.MDCMenu.attachTo(document.querySelector('.mdc-menu'));
    menu.setAbsolutePosition(200, 100);

    const menuBtn = document.querySelector('.gws-top-search-bar--show-menu-btn');
    menuBtn.addEventListener('click', (event) => {
        menu.open = true;
    })

    GView.upgradeAll()
    progressBar.close()
})