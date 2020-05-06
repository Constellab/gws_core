#
# Python GWS view
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
#

import asyncio
import json
from gws.prism.base import Base

class Controller(Base):
    views = dict()
    routes = [
       "/{action}/{uri}/{params}",
    ] 

    @classmethod
    async def action(cls, request: 'Request') -> list:
        """
            Deal with user actions
            Receive a request through a request url
            * url = /{action}/{uri|id}/{params}
                * action:
                    - update_view:  to update the current active view
                    - create_view:  to create a new view using params
                    - run_proc:     to run the current process and return the result view
                * uri|id: 
                    - uri|id of the model on which the action is applied (view_model|resource)
                * params: parameter ins JSON format    
                    e.g.:
                    create_view_params = {
                        "view": "full.classname.of.the.new.view.to.create",
                        ...
                    } 

                    run_proc_params = {
                        "name": "<process name>",
                        "input":{
                            "resource_id": "<resource_id>",
                            "resource_type": "<resource_type>"
                        }
                    } 
        """
        action = request.query_params.get('action','')
        uri = request.query_params.get('uri','')
        params = request.query_params.get('params','{}')

        try:
            params = json.loads(params)
        except:
            raise Exception(type(cls).__name__, "action", "The params is not a valid JSON text")
        

        view = cls.get_view(uri)

        if action == "update_view":
            return view.render(params)
        if action == "create_view":
            if view is None:
                raise Exception(type(cls).__name__, "action", "It seems that this request comes form an undefined view")
            else:
                #try to generate a new view
                view_name = params["view"]
                params = params["params"]
                view = view.model.create_view_instance(view_name)
                return view.render(params)

        elif action == "run":
            #run a process and render its view
            pass

        # if isinstance(model, ViewModel):
        #     # only show a view rendering
        #     view_name = params["view_name"]
        #     view = model.create_view_instance(view_name)
        #     return [ view.render(params) ]
        # elif isinstance(model, Process):
        #     # run action
        #     proc = model
        #     port_name = proc.input.get_port_names()[0]

        #     input_resource_id = params["input_resource_id"]
        #     input_resource_type = params["resource_type"]

        #     proc.input[port_name] = XXX
        #     asyncio.run( proc.run(params) )

        #     #return the views on the results
        #     view_list = []
        #     view_params = params.get('view_params', None)

        #     if view_params is None:
        #         return [ "" ]
        #     else:
        #         for k in proc.output.get_port_names():
        #             rendering = proc.output[k]._deal(view_params)[0]
        #             view_list.append( rendering )
        else:
            return ""

    @classmethod
    def get_view(cls, uri: str) -> 'View':
        return cls.views.get(uri, None)

    @classmethod
    def register(cls, view: 'View'):
        """
            Each view is uniquely registered in the system using the UUID of it view_model
        """
        cls.views[view.uri] = view