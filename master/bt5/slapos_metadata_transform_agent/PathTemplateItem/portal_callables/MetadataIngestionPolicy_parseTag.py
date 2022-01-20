"""
  This script is used in Ingestion Policy objects to parse provided by fluentd / ebulk reference.
  In this case it expects a reference in this format for example:


"""
context.log(reference)
if not reference:
  raise ValueError('reference is None')


return {'resource_reference' : reference,
        'specialise_reference': reference,
        'reference': reference   }
