var FolderTreeModule = require('../folder-tree.module.js');

export function makeFolderSelector($folder_selector, current_folder_id) {
    $folder_selector.empty();

    // recursively populate select ...
    function addChildren(node, depth) {
        for (var i = 0; i < node.children.length; i++) {
            var childNode = FolderTreeModule.folderTree.get_node(node.children[i]);

            // For each node, we create an <option> using text() for the folder name,
            // and then prepend some &nbsp; to show the tree structure using html().
            // Using html for the whole thing would be an XSS risk.
            $folder_selector.append(
                $("<option/>", {
                    value: childNode.data.folder_id,
                    text: childNode.text.trim(),
                    selected: childNode.data.folder_id == current_folder_id
                }).prepend(
                    new Array(depth).join('&nbsp;&nbsp;') + '- '
                )
            );

            // recurse
            if (childNode.children && childNode.children.length) {
                addChildren(childNode, depth + 1);
            }
        }
    }
    addChildren(FolderTreeModule.folderTree.get_node('#'), 1);
}
