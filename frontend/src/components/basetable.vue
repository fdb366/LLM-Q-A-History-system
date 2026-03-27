<template>
  <div class="base-table">
    <el-table :data="tableData" v-bind="tableConfig" :max-height="maxHeight" class="custom-table" @selection-change="handleSelectionChange" @row-click="handleRowClick">
      <el-table-column v-if="showSelection" type="selection" width="55" :fixed="showSelection && fixed ? fixed : 'none'" />
      <template v-for="column in tableColumns" :key="column.prop || column.type">
        <el-table-column v-bind="column" :show-overflow-tooltip="tableConfig.showOverflowTooltip">
          <template #default="{ row, $index }">
            <template v-if="column.type === 'index'">
              {{ $index + 1 }}
            </template>
            <template v-else-if="column.slot">
              <slot :name="column.slot" :row="row" :index="$index"></slot>
            </template>
            <template v-else>
              {{ column.formatter ? column.formatter(row) : $nullValue(row[column.prop]) }}
            </template>
          </template>
        </el-table-column>
      </template>
    </el-table>

    <div class="pagination-container" v-if="total > 0">
      <el-pagination
        v-model:current-page="currentPageValue"
        v-model:page-size="pageSizeValue"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, prev, pager, next, sizes, jumper"
        @size-change="handleSizeChange"
        prev-text="上一页"
        next-text="下一页"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from "vue";

const props = defineProps({
  tableData: {
    type: Array,
    default: () => [],
  },
  tableColumns: {
    type: Array,
    required: true,
    validator: (columns) => {
      return columns.every(column => {
        return column.prop || column.type || column.slot;
      });
    },
  },
  tableConfig: {
    type: Object,
    default: () => {
      const defaultConfig = {
        border: true,
        stripe: false,
        class: 'custom-table',
        headerRowClassName: 'table-th',
        emptyText: '暂无数据',
        style: { width: '100%' },
        showOverflowTooltip: true,
      }
      return defaultConfig
    },
    validator: (value) => {
      const defaultConfig = {
        border: true,
        stripe: false,
        class: 'custom-table',
        headerRowClassName: 'table-th',
        emptyText: '暂无数据',
        style: { width: '100%' },
        showOverflowTooltip: true,
      }
      return { ...defaultConfig, ...value }
    },
  },
  // 是否显示选择框
  showSelection: {
    type: Boolean,
    default: false,
  },
  fixed: {
    type: String,
    default: 'none',
  },
  total: {
    type: Number,
    default: 0,
  },
  // 当前页码
  currentPage: {
    type: Number,
    default: 1,
  },
  // 每页条数
  pageSize: {
    type: Number,
    default: 10,
  },
  // 表格最大高度，由父组件传入，超出显示滚动条
  maxHeight: {
    type: [Number, String],
    default: undefined,
  },
});

const emit = defineEmits(['size-change', 'current-change', 'selection-change', 'row-click']);

const currentPageValue = ref(props.currentPage);
const pageSizeValue = ref(props.pageSize);

// 监听外部传入的分页参数变化
watch(() => props.currentPage, (newVal) => {
  currentPageValue.value = newVal;
});

watch(() => props.pageSize, (newVal) => {
  pageSizeValue.value = newVal;
});

/**
 * @description 处理选择变化
 * @param {Array} selection - 已选择的行数据
 * @returns {void}
 */
const handleSelectionChange = (selection) => {
  emit('selection-change', selection);
};

/**
 * @description 处理每页条数变化
 * @param {number} val - 每页条数
 * @returns {void}
 */
const handleSizeChange = (val) => {
  pageSizeValue.value = val;
  emit('size-change', val);
};

/**
 * @description 处理页码变化
 * @param {number} val - 页码
 * @returns {void}
 */
const handleCurrentChange = (val) => {
  currentPageValue.value = val;
  emit('current-change', val);
};

/**
 * @description 处理表格行点击事件
 * @param {Object} row - 当前行数据
 * @param {Object} column - 当前列数据
 * @param {Event} event - 点击事件对象
 * @returns {void}
 */
const handleRowClick = (row, column, event) => {
  emit('row-click', row, column, event);
};
</script>

<style lang="scss" scoped>
$font-color: #262626;
$th-color: #333333;
$td-color: #666666;
.base-table {
  background: #fff;
  border-radius: 2px 2px 0px 0px;
  width: 100%;
  &.round-table {    
    border-radius: 8px 8px 0px 0px;
  }
  :deep(.el-table) {
    width: 100% !important;
    .cell {
      font-size: 14px;
      padding: 0 5px;
      color: $td-color;
    }
    &.custom-table {
      .table-th {
        border: 0px;
        th {
          box-shadow: none;
          border-bottom: 1px solid #EDEDED;
          background: #F6F7F8;
          .cell {
            font-weight: 500;
            color: $th-color;
            padding:0 2px
          }
        }

      }
    }
    .no-border {
      border: none !important;
    }
  }

  .pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }

  :deep(.el-pagination) {
    .el-pager li {
      width: 36px;
      height: 36px;
      line-height: 32px;
      margin: 0 4px;
      border-radius: 4px;
      border:  1px solid #D9DCE2;
    }

    .el-pager li.is-active {
      border-radius: 4px;
      border:  1px solid #00BB7D;
    }
    .more {
      border:0px
    }
    .el-pagination__prev,
    .el-pagination__next {
      min-width: 32px;
      height: 32px;
      line-height: 32px;
      border-radius: 4px;
    }

    .el-pagination__sizes .el-input__wrapper {
      box-shadow: none;
    }

    .el-pagination__jump {
      margin-left: 16px;
      color: $font-color;
    }
    .btn-prev{
      color: $font-color;
      border: 1px solid #D9DCE2;
      width: 74px;
      font-size: 14px;
      height: 36px;
      border-radius: 4px;
      margin-right: 8px;
    }
    .btn-next{
      color: $font-color;
      border: 1px solid #D9DCE2;
      width: 74px;
      font-size: 14px;
      height: 36px;
      border-radius: 4px;
      margin: 0 8px;
    }
    .el-pagination__jump .el-input-number .el-input__wrapper {
      box-shadow: none;
    }
    .el-pagination__sizes{
      margin-left: 0 !important; /* 正确写法：0与!important之间无间隔 */
    }
    .el-select {
      width: 88px;
      height: 36px;
    }
    .el-select__wrapper {
      height: 36px;
      width: 100px;
    }
    .el-select__placeholder{
      color: $font-color;
    }
}
}
</style>
