import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowLeft, faEdit, faShieldAlt, faTrash, faEnvelope, faPhone, faMapMarkerAlt, faCalendarAlt, faTruck } from '@fortawesome/free-solid-svg-icons';
import StarRating from './StarRating';

const ProviderDetail = ({ provider, handleVerifyProvider, handleDeleteProvider }) => {
  const [formattedDate, setFormattedDate] = useState('');

  useEffect(() => {
    const formatted = formatDate(provider?.last_active || '');
    setFormattedDate(formatted);
  }, [provider?.last_active]);

  const formatDate = (date) => {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(date).toLocaleDateString(undefined, options);
  };

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'verified':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="px-4 py-6">
      {/* Header Section */}
      <div className="mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between">
          <div className="flex items-center mb-4 md:mb-0">
            <Link to="/admin/providers" className="text-blue-600 hover:text-blue-800 mr-4">
              <FontAwesomeIcon icon={faArrowLeft} />
            </Link>
            <h2 className="text-xl font-semibold">Provider Details</h2>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link
              to={`/admin/providers/${provider?.id}/edit`}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md flex items-center"
            >
              <FontAwesomeIcon icon={faEdit} className="mr-2" />
              Edit Provider
            </Link>
            {provider?.verification_status !== 'verified' && (
              <button
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md flex items-center"
                onClick={handleVerifyProvider}
              >
                <FontAwesomeIcon icon={faShieldAlt} className="mr-2" />
                Verify
              </button>
            )}
            <button
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md flex items-center"
              onClick={handleDeleteProvider}
            >
              <FontAwesomeIcon icon={faTrash} className="mr-2" />
              Delete
            </button>
          </div>
        </div>
      </div>
      
      {/* Provider Summary Card */}
      <div className="bg-white shadow-sm rounded-lg overflow-hidden mb-6 p-6">
        <div className="flex flex-col md:flex-row">
          <div className="md:w-1/4 mb-6 md:mb-0 flex justify-center md:justify-start">
            <div className="h-32 w-32 bg-gray-200 rounded-full flex items-center justify-center">
              {provider?.service_image ? (
                <img 
                  src={provider.service_image} 
                  alt={provider.company_name} 
                  className="h-full w-full object-cover rounded-full"
                />
              ) : (
                <FontAwesomeIcon icon={faTruck} className="text-gray-500 text-4xl" />
              )}
            </div>
          </div>
          <div className="md:w-3/4">
            <div className="flex flex-col md:flex-row md:justify-between">
              <div>
                <h3 className="text-2xl font-bold text-gray-900">{provider?.company_name}</h3>
                <div className="flex items-center mt-2">
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusBadgeClass(provider?.verification_status || '')}`}>
                    {provider?.verification_status}
                  </span>
                </div>
              </div>
              <div className="mt-4 md:mt-0">
                <div className="flex items-center mb-2">
                  <StarRating rating={provider?.average_rating || 0} />
                  <span className="ml-2 text-sm text-gray-500">({provider?.completed_bookings_count} Jobs)</span>
                </div>
                <div className="text-sm text-gray-500">
                  <FontAwesomeIcon icon={faCalendarAlt} className="mr-1" /> 
                  Last Active: {formattedDate}
                </div>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
              <div className="flex items-start">
                <FontAwesomeIcon icon={faEnvelope} className="text-gray-400 mt-1 mr-3" />
                <div>
                  <div className="text-xs text-gray-500">Email</div>
                  <div className="text-sm">{provider?.user.email}</div>
                </div>
              </div>
              <div className="flex items-start">
                <FontAwesomeIcon icon={faPhone} className="text-gray-400 mt-1 mr-3" />
                <div>
                  <div className="text-xs text-gray-500">Phone</div>
                  <div className="text-sm">{provider?.user.phone}</div>
                </div>
              </div>
              <div className="flex items-start">
                <FontAwesomeIcon icon={faMapMarkerAlt} className="text-gray-400 mt-1 mr-3" />
                <div>
                  <div className="text-xs text-gray-500">Service Areas</div>
                  <div className="text-sm">
                    {provider?.operating_areas?.join(', ') || 'Not specified'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Rest of the component remains the same, but update data references */}
      {/* For example: */}
      {/* - provider.businessInfo -> provider.business_type, provider.company_reg_number, etc. */}
      {/* - provider.contactPerson -> provider.contact_person_name, provider.contact_person_email, etc. */}
      {/* - provider.bankDetails -> provider.bank_account_holder, provider.bank_name, etc. */}
      {/* - provider.documents -> provider.documents */}
      {/* - provider.reviews -> provider.reviews */}
      {/* - provider.payments -> provider.payments */}
      
    </div>
  );
};

export default ProviderDetail; 