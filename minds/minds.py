from typing import List, Union

from minds.datasources import Datasource, DatabaseConfig


class Mind:
    def __init__(
        self, client, name,
        model_name=None,
        provider=None,
        parameters=None,
        datasources=None,
        created_at=None,
        updated_at=None,
        **kwargs
    ):
        self.api = client.api
        self.client = client
        self.project = 'mindsdb'

        self.name = name
        self.model_name = model_name
        self.provider = provider
        self.parameters = parameters
        self.created_at = created_at
        self.updated_at = updated_at

        self.datasources = []
        for name in datasources:
            try:
                ds = self.client.datasources.get(name)
            except RuntimeError:
                # TODO skipped, it could be not sql skill
                continue
            self.datasources.append(ds)

    def update(
        self,
        model_name=None,
        provider=None,
        parameters=None,
        datasources=None
    ):
        if datasources:
            datasources = [ds.model_dump() for ds in datasources]

        self.api.patch(
            f'/projects/{self.project}/minds',
            data={
                'name': self.name,
                'model_name': model_name,
                'provider': provider,
                'parameters': parameters,
                'datasources': datasources,
            }
        )

    def add_datasource(self, datasource: Datasource):
        self.api.post(
            f'/projects/{self.project}/minds/{self.name}/datasources',
            data=datasource.model_dump()
        )
        updated = self.client.minds.get(self.name)

        self.datasources = updated.datasources

    def del_datasource(self, datasource: Union[Datasource, str]):
        raise NotImplementedError


class Minds:
    def __init__(self, client):
        self.api = client.api
        self.client = client

        self.project = 'mindsdb'

    def list(self) -> List[Mind]:
        data = self.api.get(f'/projects/{self.project}/minds').json()
        minds_list = []
        for item in data:
            minds_list.append(Mind(self.client, **item))
        return minds_list

    def get(self, name: str) -> Mind:
        item = self.api.get(f'/projects/{self.project}/minds/{name}').json()
        return Mind(self.client, **item)

    def create(
        self, name,
        model_name=None,
        provider=None,
        parameters=None,
        datasources=None,
        replace=False,
    ) -> Mind:

        if replace:
            try:
                self.drop(name)
            except Exception:
                ...

        ds_names = []
        if datasources:
            for ds in datasources:
                if isinstance(ds, Datasource):
                    ds = ds.name
                elif isinstance(ds, DatabaseConfig):
                    # try to create
                    try:
                        self.client.datasources.create(ds)
                    except Exception:
                        ...
                    ds = ds.name
                elif not isinstance(ds, str):
                    raise ValueError(f'Unknown type of datasource: {ds}')
                ds_names.append(ds)

        self.api.post(
            f'/projects/{self.project}/minds',
            data={
                'name': name,
                'model_name': model_name,
                'provider': provider,
                'parameters': parameters,
                'datasources': ds_names,
            }
        )
        mind = self.get(name)

        return mind

    def drop(self, name: str):
        mind = self.get(name)
        # TODO not implemented yet
        # for ds in mind.datasources:
        #     mind.del_datasource(ds)

        self.api.delete(f'/projects/{self.project}/minds/{name}')
