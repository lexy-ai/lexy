import React from "react";
import {Handle, type Node, NodeToolbar, Position} from "reactflow";
import {type Collection} from '~/types/collectionTypes';
import {
    ArrowRightStartOnRectangleIcon,
    CircleStackIcon,
    DocumentChartBarIcon
} from "@heroicons/react/24/outline";

interface CollectionNodeData {
    collection: Collection;
    toolbarVisible?: boolean;
}

export type CollectionNodeProps = Node<CollectionNodeData>
// export interface CollectionNodeProps extends NodeProps {
//     // You can add additional properties here if needed
//     data: CollectionNodeData;
// }

// Custom Collection Node
const CollectionNode: React.FC<CollectionNodeProps> = ({data,}) => {
    const collection = data.collection;
    return (
        <div className="bg-white rounded-lg p-4 shadow-md border border-gray-200">
            {/* optionally include a toolbar for this node */}
            <NodeToolbar isVisible={data.toolbarVisible} position={Position.Bottom}>
                <button onClick={() => alert("Document stats view")}><DocumentChartBarIcon
                    className="h-4 w-4 hover:text-rose-500"/></button>
                <button onClick={() => alert("Add binding")}><ArrowRightStartOnRectangleIcon
                    className="h-4 w-4 hover:text-rose-500"/></button>
            </NodeToolbar>
            <div className="flex items-center justify-center">
                <CircleStackIcon className="h-4 w-4 text-indigo-600 mr-2"/>
                <span className="text-xs font-semibold">{collection.collection_name}</span>
            </div>
            <Handle type="source" position={Position.Right}/>

        </div>
    );
};

export default CollectionNode;
