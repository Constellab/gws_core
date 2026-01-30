

/**
 * Factory function to create custom tools for the rich text editor.
 * @param {object} authenticationInfo - Authentication information passed from the component
 * @returns {object} Custom tools configuration object
 */
export function getCustomTools(config, authenticationInfo) {

  class DcTextEditorToolExampleBlock {

    constructor({data}){
      this.data = data;
    }

    static get toolbox() {
      return {
        title: 'Example Tool',
        icon: '<span class="material-icons-outlined">build</span>',
      }
    }

    /**
     * Render a div with a <p> showing the count from the API
     */
    render() {
      const wrapper = document.createElement('div');
      const p = document.createElement('p');
      p.innerText = `Custom block content : '${this.data?.text || 'default text'}'`;
      wrapper.appendChild(p);

      return wrapper;
    }

    save(block) {
      return {data: this.data?.text || 'default text' };
    }
  }


  return { [config.customBlocks.CustomBlock]: DcTextEditorToolExampleBlock };
}