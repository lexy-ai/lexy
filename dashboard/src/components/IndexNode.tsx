import React from "react";
import {Handle, Position, type Node, NodeToolbar} from "reactflow";
import {type Index} from '~/types/indexTypes';
import {
    ArrowLeftStartOnRectangleIcon,
    MagnifyingGlassIcon,
    TableCellsIcon
} from "@heroicons/react/24/outline";

interface IndexNodeData {
    index: Index;
    toolbarVisible?: boolean;
}

export type IndexNodeProps = Node<IndexNodeData>
// export interface IndexNodeProps extends NodeProps {
//     // You can add additional properties here if needed
//     data: IndexNodeData;
// }

// Custom Index Node
const IndexNode: React.FC<IndexNodeProps> = ({data}) => {
    const index = data.index;
    return (
        <div className="bg-white rounded-lg p-4 shadow-md border border-gray-200">
            <div className="flex items-center justify-center border-b pb-2">
                {/* optionally include a toolbar for this node */}
                <NodeToolbar isVisible={data.toolbarVisible} position={Position.Bottom}>
                    <button onClick={() => alert("Add binding")}><ArrowLeftStartOnRectangleIcon
                        className="h-4 w-4 hover:text-rose-500"/></button>
                    <button onClick={() => alert("View data")}><MagnifyingGlassIcon
                        className="h-4 w-4 hover:text-rose-500"/></button>
                </NodeToolbar>
                <TableCellsIcon className="h-4 w-4 text-emerald-700 mr-2"/>
                <span className="text-xs font-semibold">{index.index_id}</span>
            </div>
            <Handle type="target" position={Position.Left}/>
            <ul className="pt-2">
                {Object.entries(index.index_fields).map(([fieldName, details]) => (
                    <li className="text-xs" key={fieldName}>
                        <span className="text-xs font-medium">{fieldName}</span>: <span
                        className="text-xs font-light">{details.type}</span>
                        {details.extras && (
                            <ul>
                                {Object.entries(details.extras).map(([key, value]) => (
                                    <li className="text-xs font-light pl-4" key={key}>
                                        <span className="text-xs">{key}</span>: {value.toString()}
                                    </li>
                                ))}
                            </ul>
                        )}
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default IndexNode;
