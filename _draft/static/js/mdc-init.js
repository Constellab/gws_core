window.addEventListener("load", function () {
    //tdrawer
    const drawer = mdc.drawer.MDCDrawer.attachTo(document.querySelector('.mdc-drawer'));
    const progressBar = mdc.linearProgress.MDCLinearProgress.attachTo(document.querySelector('.mdc-linear-progress'));
    progressBar.open()

    const listEl = document.querySelector('.mdc-drawer .mdc-list');
    listEl.addEventListener('click', (event) => {
        drawer.open = false;
    });

    /*const mainContentEl = document.querySelector('.main-content');
    document.body.addEventListener('MDCDrawer:closed', () => {
        mainContentEl.querySelector('input, button').focus();
    });*/

    //components
    mdc.topAppBar.MDCTopAppBar.attachTo(document.querySelector('.mdc-top-app-bar'));
    initAllMdcComponents()

    const sidebarBtn = document.querySelector('.gws-top-bar--open-sidebar-btn');
    sidebarBtn.addEventListener('click', (event) => {
        drawer.open = true;
    });

    const menu = mdc.menu.MDCMenu.attachTo(document.querySelector('.mdc-menu'));
    const menuBtn = document.querySelector('.gws-top-search-bar--show-menu-btn');
    menuBtn.addEventListener('click', (event) => {
        menu.open = true;
    })

    GView.upgradeAll()
    progressBar.close()
})

function initAllMdcComponents(){
    [].map.call(document.querySelectorAll('.mdc-menu'), function(el) { mdc.menu.MDCMenu.attachTo(el); });
    [].map.call(document.querySelectorAll('.mdc-fab'), function(el) { mdc.ripple.MDCRipple.attachTo(el); });
    [].map.call(document.querySelectorAll('.mdc-data-table'), function(el) { mdc.dataTable.MDCDataTable.attachTo(el); });
    const selector = '.mdc-button, .mdc-icon-button, .mdc-card__primary-action';
    [].map.call(document.querySelectorAll(selector), function(el) { mdc.ripple.MDCRipple.attachTo(el); });
    [].map.call(document.querySelectorAll('.mdc-tab-bar'), function(el) { mdc.tabBar.MDCTabBar.attachTo(el); });
}