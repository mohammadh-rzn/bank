from drf_yasg.generators import OpenAPISchemaGenerator

class BothHttpAndHttpsSchemaGenerator(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        schema.schemes = ["http", "https"]
        return schema
from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg import openapi

class CompleteSchemaGenerator(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        
        # Ensure all components are included in YAML
        schema.components = openapi.Components(
            schemas=self.get_serializer_definitions(),
            securitySchemes=self.get_security_definitions()
        )
        return schema