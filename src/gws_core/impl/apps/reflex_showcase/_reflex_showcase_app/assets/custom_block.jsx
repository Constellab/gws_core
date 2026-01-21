
import { DcHttpService } from '/public/external/browser/dc-reflex.js';

/**
 * Factory function to create custom tools for the rich text editor.
 * @param {object} authenticationInfo - Authentication information passed from the component
 * @returns {object} Custom tools configuration object
 */
export function getCustomTools(authenticationInfo) {

  class DcTextEditorToolExampleBlock {
    static get toolbox() {
      return {
        title: 'Example Tool',
        icon: '<span class="material-icons-outlined">home</span>',
      }
    }

    /**
     * Render a div with a <p> showing the count from the API
     */
    render() {
      const wrapper = document.createElement('div');
      const p = document.createElement('p');
      p.innerText = 'Loading...';
      wrapper.appendChild(p);

      console.log('Fetching count from API...', authenticationInfo);

      const httpService = new DcHttpService(authenticationInfo?.app_id || '', authenticationInfo?.user_access_token || '');

      // TODO change the endpoint as needed
      httpService.get('resource/count/count', {
        headers: {
          'gws_user_access_token': authenticationInfo?.user_access_token || '',
          'gws_app_id': authenticationInfo?.app_id || '',
        },
      })
        .then(data => {
          p.innerText = `Count: ${data.count}`;
        })
        .catch((err) => {
          console.error('Error fetching count:', err);
          p.innerText = 'Error loading count';
        });

      return wrapper;
    }

    save(block) {
      return {data: 'example data' };
    }
  }

  console.log('Custom block loaded: DcTextEditorToolExampleBlock');
  return {example: DcTextEditorToolExampleBlock};
}