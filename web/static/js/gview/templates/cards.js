new GViewTemplate({
    class: "gview:card",
    render: function (data) {
        function _card(container, data){
            data.style = data.style || ""
            data.title = data.title || ""
            data.body = data.body || ""
            container.innerHTML = `
                <div class="demo-card-wide mdl-card mdl-shadow--2dp">
                    <div class="mdl-card__title">
                        <h2 class="mdl-card__title-text">`+data.title+`</h2>
                    </div>
                    <div class="mdl-card__supporting-text">
                        `+data.body+`
                    </div>
                    <div class="mdl-card__menu">
                        <button class="mdl-button mdl-button--icon mdl-js-button mdl-js-ripple-effect">
                            <i class="material-icons">share</i>
                        </button>
                    </div>
                </div>
            `;
            componentHandler.upgradeDom();
        }
        return _card
    }
})