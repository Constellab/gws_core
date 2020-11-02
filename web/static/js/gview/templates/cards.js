new GViewTemplate({
    class: "gview:card",
    render: function (data) {
        function _card(container, data){
            data.style = data.style || ""
            data.title = data.title || ""
            data.body = data.body || ""
            data.style = data.style || ""
            data.titleImg = data.titleImg || ""
            data.titleHeight = data.titleHeight || "150px"
            container.innerHTML = `
                <div class="demo-card-wide mdl-card mdl-shadow--2dp" style="`+data.style+`">
                    <div class="mdl-card__title" style="background: url('`+data.titleImg+`'); height: `+data.titleHeight+`">
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