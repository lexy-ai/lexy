import React from 'react';
// import CollectionComponent from './CollectionComponent';
// import BindingComponent from './BindingComponent';
// import IndexComponent from './IndexComponent';
import {type Collection} from '~/types/collectionTypes';
import {type Binding} from '~/types/bindingTypes';
import {type Index} from '~/types/indexTypes';

interface Props {
  collections: Collection[];
  indexes: Index[];
  bindings: Binding[];
}

const DataLists: React.FC<Props> = ({ collections, indexes, bindings }) => {
  return (
    <div className="container mx-auto p-4">
      {/* Collections Section */}
      <section className="mb-8">
        <h2 className="text-2xl font-bold mb-4">Collections</h2>
        <ul className="divide-y divide-gray-100">
          {collections.map((collection) => (
            <li key={collection.collection_id} className="py-4">
                {/* Render your collection details here */}
                <p className="text-sm font-semibold leading-6 text-gray-900">{collection.collection_name}</p>
                <p className="mt-1 truncate text-xs leading-5 text-gray-500">ID: {collection.collection_id}</p>
                <p className="mt-1 truncate text-xs leading-5 text-gray-500">Description: {collection.description}</p>
                <p className="mt-1 truncate text-xs leading-5 text-gray-500">Created At: {new Date(collection.created_at).toLocaleString()}</p>
                <p className="mt-1 truncate text-xs leading-5 text-gray-500">Updated At: {new Date(collection.updated_at).toLocaleString()}</p>
            </li>
          ))}
        </ul>
      </section>

      {/* Indexes Section */}
    <section className="mb-8">
      <h2 className="text-2xl font-bold mb-4">Indexes</h2>
      <ul className="divide-y divide-gray-100">
        {indexes.map((index) => (
          <li key={index.index_id} className="py-4 flex flex-col sm:flex-row justify-between">
            {/* Index Details */}
            <div className="flex-1">
              <p className="text-sm font-semibold leading-6 text-gray-900">{index.index_id}</p>
              <p className="mt-1 truncate text-xs leading-5 text-gray-500">Description: {index.description}</p>
              <p className="mt-1 truncate text-xs leading-5 text-gray-500">Table name: {index.index_table_name}</p>
            </div>
            {/* Fields */}
            <div className="flex-1 mt-4 sm:mt-0">
              <ul>
                {Object.entries(index.index_fields).map(([fieldName, details]) => (
                  <li className="text-xs" key={fieldName}>
                    <span className="font-medium">{fieldName}</span>: <span className="font-light">{details.type}</span>
                    {details.extras && (
                      <ul>
                        {Object.entries(details.extras).map(([key, value]) => (
                          <li className="text-xs font-light pl-4" key={key}>
                            <span>{key}</span>: {value.toString()}
                          </li>
                        ))}
                      </ul>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          </li>
        ))}
      </ul>
    </section>


      {/* Bindings Section */}
    <section className="mb-8">
      <h2 className="text-2xl font-bold mb-4">Bindings</h2>
      <ul className="divide-y divide-gray-100">
        {bindings.map((binding) => (
          <li key={binding.binding_id} className="py-4 flex flex-col md:flex-row justify-between">
            {/* Left Column: Binding Details */}
            <div className="flex-1">
              <p className="text-sm font-semibold leading-6 text-gray-900">ID: {binding.binding_id}</p>
                <p className="mt-1 truncate text-xs leading-5 text-gray-500">Created At: {new Date(binding.created_at).toLocaleString()}</p>
                <p className="mt-1 truncate text-xs leading-5 text-gray-500">Updated At: {new Date(binding.updated_at).toLocaleString()}</p>
            </div>
            {/* Right Column: Collection, Transformer, and Index */}
            <div className="flex-1 mt-4 md:mt-0">
              <p className="mt-1 truncate text-xs leading-5 text-gray-500">Collection: <span className="font-medium text-gray-900">{binding.collection.collection_name}</span></p>
              <p className="mt-1 truncate text-xs leading-5 text-gray-500">Transformer: <span className="font-medium text-gray-900">{binding.transformer_id}</span></p>
              <p className="mt-1 truncate text-xs leading-5 text-gray-500">Index: <span className="font-medium text-gray-900">{binding.index_id}</span></p>
              {/* Include other details as necessary */}
            </div>
          </li>
        ))}
      </ul>
    </section>
    </div>
  );
};

export default DataLists;
