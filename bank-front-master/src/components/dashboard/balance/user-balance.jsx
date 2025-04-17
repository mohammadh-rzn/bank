import React, { useEffect, useState } from 'react';
import { Card, Input, Button, Form, message, Typography, Row, Col } from 'antd';
import { fetchBalance, transferMoney } from './user-balance-api';

const { Title, Text } = Typography;

const UserBalance = () => {
    const [balance, setBalance] = useState(null);
    const [loading, setLoading] = useState(false);
    const [form] = Form.useForm();

    useEffect(() => {
        getBalance();
    }, []);

    const getBalance = async () => {
        try {
            const data = await fetchBalance();
            setBalance(data?.balance || 0);
        } catch (error) {
            message.error('Failed to fetch balance.');
        }
    };

    const handleTransfer = async (values) => {
        setLoading(true);
        try {
            const response = await transferMoney(values.amount, values.recipient_id);
            if (response?.message !== 'Transfer successful') {
                message.error('Transfer failed!');
            }
            else {
                message.success('Transfer successful!');
            }
            form.resetFields();
            await getBalance();
        } catch (error) {
            message.error('Transfer failed.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ height: '100vh', padding: '24px' }}>
            <Card style={{ height: '100%' }}>
                <Row style={{ height: '100%' }} gutter={32}>
                    <Col
                        xs={24}
                        md={10}
                        style={{
                            display: 'flex',
                            flexDirection: 'column',
                            justifyContent: 'center',
                            paddingLeft: '150px',
                            gap: '16px',
                        }}
                    >
                        <Title level={3} style={{ margin: 0 }}>Current Balance</Title>
                        <Text strong style={{ fontSize: '36px', color: '#52c41a', margin: 0 }}>
                            ${parseFloat(balance).toFixed(2)}
                        </Text>
                    </Col>

                    <Col xs={24} md={14}>
                        <Title level={4}>Transfer Money</Title>
                        <Form
                            form={form}
                            layout="vertical"
                            onFinish={handleTransfer}
                            style={{ marginTop: 20, maxWidth: 400 }}
                        >
                            <Form.Item
                                label="Recipient ID"
                                name="recipient_id"
                                rules={[{ required: true, message: 'Please enter recipient ID' }]}
                            >
                                <Input placeholder="Enter recipient ID" />
                            </Form.Item>

                            <Form.Item
                                label="Amount"
                                name="amount"
                                rules={[{ required: true, message: 'Please enter amount' }]}
                            >
                                <Input type="number" placeholder="Enter amount to transfer" />
                            </Form.Item>

                            <Form.Item>
                                <Button type="primary" htmlType="submit" loading={loading} block>
                                    Transfer
                                </Button>
                            </Form.Item>
                        </Form>
                    </Col>
                </Row>
            </Card>
        </div>
    );
};

export default UserBalance;
