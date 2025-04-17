import api from '../../../config/axios-interceptor';

export const fetchBalance = async () => {
    try {
        return await api.get(
            `/api/balance/`,
        );
    } catch (error) {
        console.error('Error during API call:', error);
    }
};

export const transferMoney = async (amount, recipient_id) => {
    try {
        return await api.post(
            `/api/transfer/`,
            {
                amount: amount,
                recipient_id: recipient_id
            }
        );
    } catch (error) {
        console.error('Error during API call:', error);
    }
};