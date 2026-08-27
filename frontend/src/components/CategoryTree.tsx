"use client";

import { CategoryTreeNode } from "@/lib/api";

export function CategoryTree({
  nodes,
  onSelect,
  selectedId,
  showInactive = false,
}: {
  nodes: CategoryTreeNode[];
  onSelect?: (node: CategoryTreeNode) => void;
  selectedId?: string | null;
  showInactive?: boolean;
}) {
  if (!nodes.length) {
    return <p className="text-sm text-gray-500">No categories yet.</p>;
  }

  return (
    <ul className="space-y-1">
      {nodes.map((node) => (
        <CategoryNode key={node.id} node={node} onSelect={onSelect} selectedId={selectedId} depth={0} showInactive={showInactive} />
      ))}
    </ul>
  );
}

function CategoryNode({
  node,
  onSelect,
  selectedId,
  depth,
  showInactive,
}: {
  node: CategoryTreeNode;
  onSelect?: (node: CategoryTreeNode) => void;
  selectedId?: string | null;
  depth: number;
  showInactive: boolean;
}) {
  const isSelected = selectedId === node.id;
  return (
    <li>
      <div
        className={`flex items-center gap-2 px-2 py-1.5 rounded cursor-pointer text-sm ${isSelected ? "bg-indigo-50 text-indigo-700 border border-indigo-200" : "hover:bg-gray-50 text-gray-800"} ${!node.is_active ? "opacity-60" : ""}`}
        style={{ marginLeft: depth * 16 }}
        onClick={() => onSelect?.(node)}
      >
        <span className="flex-1 flex items-center gap-2">
          {node.children.length > 0 ? (
            <span className="text-gray-400">▾</span>
          ) : (
            <span className="text-gray-300">•</span>
          )}
          <span className="font-medium">{node.name}</span>
          <span className="text-xs text-gray-500">/{node.slug}</span>
          {!node.is_active && <span className="text-xs px-1.5 py-0.5 bg-gray-200 rounded">inactive</span>}
        </span>
        {!showInactive && <span className="text-xs text-gray-400">{node.children.length > 0 ? `${node.children.length} sub` : ""}</span>}
      </div>
      {node.children.length > 0 && (
        <ul className="mt-1 space-y-1">
          {node.children.map((child) => (
            <CategoryNode key={child.id} node={child} onSelect={onSelect} selectedId={selectedId} depth={depth + 1} showInactive={showInactive} />
          ))}
        </ul>
      )}
    </li>
  );
}

export function flattenTree(nodes: CategoryTreeNode[]): { id: string; name: string; slug: string; depth: number; node: CategoryTreeNode }[] {
  const out: { id: string; name: string; slug: string; depth: number; node: CategoryTreeNode }[] = [];
  function walk(list: CategoryTreeNode[], depth: number) {
    for (const n of list) {
      out.push({ id: n.id, name: n.name, slug: n.slug, depth, node: n });
      if (n.children.length) walk(n.children, depth + 1);
    }
  }
  walk(nodes, 0);
  return out;
}
