import React, {useCallback, useEffect} from 'react';
import ReactFlow, {
  addEdge,
  Background,
  BackgroundVariant,
  type Connection,
  type Edge,
  PanOnScrollMode,
  useEdgesState,
  useNodesState,
} from 'reactflow';
import {type Collection} from '~/types/collectionTypes';
import {type Binding} from '~/types/bindingTypes';
import {type Index} from '~/types/indexTypes';
import CollectionNode, {type CollectionNodeProps} from '~/components/CollectionNode';
import IndexNode, {type IndexNodeProps} from '~/components/IndexNode';
import BindingEdge from '~/components/BindingEdge';
import {fetchBindings, fetchCollections, fetchIndexes} from "~/api/apiService";
import 'reactflow/dist/style.css';
import 'tailwind.config';

const HORIZONTAL_SPACING = 600; // Horizontal space between collections and indexes
const VERTICAL_SPACING = 200; // Vertical space between different collections or indexes
const INDEX_VERTICAL_SPACING = 175; // Vertical space between indexes of the same collection

const nodeTypes = {
  collectionNode: CollectionNode,
  indexNode: IndexNode,
};

const edgeTypes = {
  bindingEdge: BindingEdge,
};

const createFlowElements = (collections: Collection[], bindings: Binding[], indexes: Index[]) => {
  let yOffset = 50; // Initial vertical offset
  const collectionNodes: CollectionNodeProps[] = [];
  const indexNodes: IndexNodeProps[] = [];
  const bindingEdges: Edge[] = [];
  const includedIndexIds = new Set(); // To track which indexes are included

  // Split collections into with and without bindings
  const collectionsWithBindings = collections.filter(collection =>
    bindings.some(binding => binding.collection_id === collection.collection_id));
  const collectionsWithoutBindings = collections.filter(collection =>
    !bindings.some(binding => binding.collection_id === collection.collection_id));

  // Function to process and position collection and its indexes
  const processCollection = (collection: Collection) => {
    // Position for collection node
    const collectionNode: CollectionNodeProps = {
      id: `collection__${collection.collection_id}`,
      type: 'collectionNode',
      position: { x: 100, y: yOffset }, // X is constant, Y varies
      data: { collection: collection },
      draggable: false,
      deletable: false,
    };
    collectionNodes.push(collectionNode);

    // Find and position indexes for this collection
    const collectionIndexes = bindings
      .filter((binding) => binding.collection_id === collection.collection_id)
      .flatMap((binding) => {
        includedIndexIds.add(binding.index_id); // Mark index as included
        return indexes.filter((index) => index.index_id === binding.index_id);
      });

    collectionIndexes.forEach((index, idx) => {
      // Position for index node
      const indexNode: IndexNodeProps = {
        id: `index__${index.index_id}`,
        type: 'indexNode',
        position: { x: 100 + HORIZONTAL_SPACING, y: yOffset }, // Align vertically
        data: { index: index },
        deletable: false
      };
      indexNodes.push(indexNode);

      // Edge from collection to index
      const binding = bindings.find((binding) =>
          binding.collection_id === collection.collection_id && binding.index_id === index.index_id);
      const edge = {
        id: `e${collection.collection_id}-${index.index_id}`,
        source: `collection__${collection.collection_id}`,
        target: `index__${index.index_id}`,
        type: 'bindingEdge',
        data: { binding: binding },
        animated: binding && binding.status === 'on',
      };
      bindingEdges.push(edge);

      // Increment yOffset after positioning each index
      if (idx < collectionIndexes.length - 1) {
        yOffset += INDEX_VERTICAL_SPACING; // Increment yOffset for the next index in this collection
      }
    });

    yOffset += VERTICAL_SPACING; // Increase yOffset for next collection, constant spacing
  };

  // Process collections with bindings first
  collectionsWithBindings.forEach(processCollection);

  // Process collections without bindings
  collectionsWithoutBindings.forEach(processCollection);

  // Reset yOffset to the y-position of the last indexNode, if it exists
  if (indexNodes.length > 0) {
    const lastNode: IndexNodeProps | undefined = indexNodes[indexNodes.length - 1];
    if (lastNode) {
      yOffset = lastNode.position.y + VERTICAL_SPACING;
    }
  }

  // Include indexes without attached binding or collection
  indexes.forEach((index) => {
    if (!includedIndexIds.has(index.index_id)) {
      const indexNode: IndexNodeProps = {
        id: `index__${index.index_id}`,
        type: 'indexNode',
        position: { x: 100 + HORIZONTAL_SPACING, y: yOffset }, // Position after last collection
        data: { index: index },
        deletable: false
      };
      indexNodes.push(indexNode);
      yOffset += VERTICAL_SPACING; // Increment yOffset for next standalone index
    }
  });

  return { nodes: [...collectionNodes, ...indexNodes], edges: bindingEdges };
};


const PipelinesPage: React.FC = () => {

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  useEffect(() => {
    const fetchData = async () => {
      try {
        const collectionsData = await fetchCollections();
        const bindingsData = await fetchBindings();
        const indexesData = await fetchIndexes();

        const { nodes: initialNodes, edges: initialEdges } = createFlowElements(
          collectionsData,
          bindingsData,
          indexesData
        );

        setNodes(initialNodes);
        setEdges(initialEdges);
      } catch (error) {
        console.error("Failed to fetch data:", error);
      }
    };

    void fetchData();
  }, []);

  return (
    <div style={{ width: '100vw', height: '100vh' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        panOnScroll={true}
        panOnScrollMode={PanOnScrollMode.Vertical}
      >
        <Background variant={BackgroundVariant.Dots} gap={16} size={1} />
      </ReactFlow>
    </div>
  );
}

export default PipelinesPage;
