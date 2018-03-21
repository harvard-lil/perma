var LinkListModule = require('./links-list.module.js');
var FolderTreeModule = require('./folder-tree.module.js');
var CreateLinkModule = require('./create-link.module.js');
var LinkBatchCreateModule = require('./link-batch-create.module.js');
var LinkBatchViewModule = require('./link-batch-view.module.js');

FolderTreeModule.init();
LinkListModule.init();
CreateLinkModule.init();
LinkBatchCreateModule.init();
LinkBatchViewModule.init();
