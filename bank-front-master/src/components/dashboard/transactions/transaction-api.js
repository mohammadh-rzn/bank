import api from '../../../config/axios-interceptor';

export const fetchTransactions = async (page = 1, pageSize = 10) => {
    try {
        return await api.get(
            `/api/transactions/?page_size=${pageSize}&page=${page}`,
        );
    } catch (error) {
        console.error('Error during API call:', error);
    }
};