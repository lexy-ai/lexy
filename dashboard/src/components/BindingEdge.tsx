import React from 'react';
import {BaseEdge, getBezierPath, EdgeLabelRenderer, type EdgeProps} from 'reactflow';
import {type Binding} from '~/types/bindingTypes';
import {
    CodeBracketIcon,
    // FunnelIcon
} from '@heroicons/react/24/outline';

interface BindingEdgeData {
    binding: Binding;
}

interface BindingEdgeProps extends EdgeProps {
    data: BindingEdgeData;
}

const BindingEdge: React.FC<BindingEdgeProps> = ({
                                                     id,
                                                     sourceX,
                                                     sourceY,
                                                     targetX,
                                                     targetY,
                                                     sourcePosition,
                                                     targetPosition,
                                                     data,
                                                 }) => {
    const [edgePath, labelX, labelY] = getBezierPath({
        sourceX,
        sourceY,
        sourcePosition,
        targetX,
        targetY,
        targetPosition,
    });
    // // Calculate a point 5% along the edge path
    // const iconX = sourceX + 0.05 * (targetX - sourceX);
    // const iconY = sourceY + 0.05 * (targetY - sourceY);

    return (
        <>
            <BaseEdge id={id} path={edgePath}/>
            <EdgeLabelRenderer>
                {/* optionally render a funnel icon if the binding has filters */}
                {/*{data.binding.filter !== null && (*/}
                {/*    <FunnelIcon*/}
                {/*        style={{*/}
                {/*            position: 'absolute',*/}
                {/*            left: `${iconX}px`,*/}
                {/*            top: `${iconY}px`,*/}
                {/*            transform: `translate(-50%, -50%)`, // Center the icon on (iconX, iconY)*/}
                {/*        }}*/}
                {/*        className="w-4 h-4 text-gray-800 hover:text-violet-500" // Adjust size as needed*/}
                {/*    />*/}
                {/*)}*/}
                <div
                    style={{
                        position: 'absolute',
                        transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
                        pointerEvents: 'all',
                    }}
                    className="nodrag nopan backdrop-blur-sm rounded-md bg-white/50 p-1"
                >
                    <button onClick={() => alert("Function view")}>
                        <CodeBracketIcon className="w-4 h-4 text-fuchsia-600 inline-block mr-2"/>
                    </button>
                    <span className="text-xs font-mono">{data.binding.transformer_id}</span>
                </div>
            </EdgeLabelRenderer>
        </>

    );
};

export default BindingEdge;
