import React, { useEffect, useState } from 'react';
import { Table, Tag } from 'antd';
import moment from 'moment';
import { fetchTransactions } from './transaction-api';

const Transactions = () => {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize, setPageSize] = useState(10);
    const [totalItems, setTotalItems] = useState(0);

    useEffect(() => {
        handleFetchTransactions(currentPage, pageSize);
    }, [currentPage, pageSize]);

    const handleFetchTransactions = async (page, size) => {
        setLoading(true);
        try {
            const response = await fetchTransactions(page, size);
            setData(response?.results || []);
            setTotalItems(response?.count || 0); // assuming your API returns "count"
        } catch (error) {
            console.error('Failed to fetch transactions:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleTableChange = (pagination) => {
        setCurrentPage(pagination.current);
        setPageSize(pagination.pageSize);
    };

    const columns = [
        {
            title: 'Type',
            dataIndex: 'transaction_type',
            key: 'transaction_type',
            align: 'center',
            render: (type) => (
                <Tag color={type === 'DEP' ? 'green' : 'volcano'}>
                    {type === 'DEP' ? 'DEPOSIT' : 'WITHDRAW'}
                </Tag>
            ),
        },
        {
            title: 'Description',
            dataIndex: 'description',
            key: 'description',
            align: 'center',
        },
        {
            title: 'Amount',
            dataIndex: 'amount',
            key: 'amount',
            align: 'center',
            render: (amount) => `$${parseFloat(amount).toFixed(2)}`,
        },
        {
            title: 'Transaction Time',
            dataIndex: 'timestamp',
            key: 'timestamp',
            align: 'center',
            render: (timestamp) =>
                moment(timestamp).format('YYYY-MM-DD HH:mm:ss'),
        },
    ];

    return (
        <div>
            <Table
                columns={columns}
                dataSource={data}
                rowKey="id"
                loading={loading}
                pagination={{
                    current: currentPage,
                    pageSize: pageSize,
                    total: totalItems,
                    showSizeChanger: true,
                    pageSizeOptions: ['2', '5', '10', '20'],
                }}
                onChange={handleTableChange}
            />
        </div>
    );
};

export default Transactions;
