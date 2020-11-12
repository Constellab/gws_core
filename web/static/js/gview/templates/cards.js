new GViewTemplate({
    class: "gview:card",
    render: function (data) {
        function _card(container, data){
            data.style = data.style || "width: 350px; height 350px;"
            data.title = data.title || ""
            data.subtitle = data.subtitle || ""
            data.body = data.body || ""
            data.style = data.style || ""
            data.titleImg = data.titleImg || ""
            data.titleHeight = data.titleHeight || ""
            container.innerHTML = `
                <div class="mdc-card" style="`+data.style+`" >
                    <div class="mdc-card__primary-action" tabindex="0">
                        <div class="mdc-card__media" style="padding: 0px 16px;">
                            <h2 class="mdc-typography mdc-typography--headline6">`+data.title+`</h2>
                            <h3 class="mdc-typography mdc-typography--subtitle2">`+data.subtitle+`</h3>
                        </div>
                        <div class="mdc-typography mdc-typography--body2" style="padding: 0px 16px;">
                            `+data.body+`
                        </div>
                    </div>
                    <div class="mdc-card__actions">
                    <div class="mdc-card__action-buttons">
                        <button class="mdc-button mdc-card__action mdc-card__action--button">  <span class="mdc-button__ripple"></span> Read</button>
                        <button class="mdc-button mdc-card__action mdc-card__action--button">  <span class="mdc-button__ripple"></span> Bookmark</button>
                    </div>
                    <div class="mdc-card__action-icons">
                        <button class="mdc-icon-button mdc-card__action mdc-card__action--icon--unbounded" aria-pressed="false" aria-label="Add to favorites" title="Add to favorites">
                        <i class="material-icons mdc-icon-button__icon mdc-icon-button__icon--on">favorite</i>
                        <i class="material-icons mdc-icon-button__icon">favorite_border</i>
                        </button>
                        <button class="mdc-icon-button material-icons mdc-card__action mdc-card__action--icon--unbounded" title="Share" data-mdc-ripple-is-unbounded="true">share</button>
                        <button class="mdc-icon-button material-icons mdc-card__action mdc-card__action--icon--unbounded" title="More options" data-mdc-ripple-is-unbounded="true">more_vert</button>
                    </div>
                    </div>
                </div>
            `;
        }
        return _card
    }
})

