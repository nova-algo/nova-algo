import React, { useState, useEffect } from "react";
import {
  Box,
  Modal,
  ModalContent,
  ModalBody,
  ModalCloseButton,
  useBreakpointValue,
  VStack,
  Heading,
  Portal,
  IconButton,
  HStack,
  ModalHeader,
  ModalOverlay,
} from "@chakra-ui/react";
import { LuXCircle } from "react-icons/lu";

interface ResponsiveModalSheetProps {
  title?: string;
  content: React.ReactNode;
  isOpen: boolean;
  onClose: () => void;
}

export const ResponsiveModalSheet: React.FC<ResponsiveModalSheetProps> = ({
  isOpen,
  onClose,

  title,
  content,
}) => {
  const [isModal, setIsModal] = useState(true);

  // Use useBreakpointValue to determine if we should show a Modal or sheet
  const variant = useBreakpointValue({ base: "sheet", md: "Modal" });

  useEffect(() => {
    setIsModal(variant === "Modal");
  }, [variant]);

  const renderContent = () => (
    <VStack align="stretch" spacing={4} p={4}>
      <Heading size="md">{title}</Heading>
      {content}
    </VStack>
  );

  return (
    <>
      <Modal
        isOpen={isOpen && isModal}
        onClose={onClose}
        closeOnOverlayClick={true}
        returnFocusOnClose={false}
      >
        <ModalOverlay />
        <ModalContent borderRadius="36px" boxShadow="lg">
          <ModalHeader>
            <ModalCloseButton />
          </ModalHeader>

          <ModalBody>{renderContent()}</ModalBody>
        </ModalContent>
      </Modal>
      {!isModal && isOpen && (
        <Portal>
          <Box
            h="100vh"
            w="100vw"
            position="fixed"
            top={0}
            left={0}
            bg={"blackAlpha.500"}
          >
            <Box
              p={4}
              color="white"
              mt="4"
              bg="white"
              roundedTop="24px"
              shadow="md"
              bottom={0}
              left={0}
              position="absolute"
              w={"full"}
              maxHeight="50vh"
              overflowY="auto"
              zIndex={1200}
            >
              <HStack justify={"flex-end"}>
                <IconButton
                  aria-label="Close"
                  fontWeight={400}
                  variant={"ghost"}
                  icon={<LuXCircle size={24} />}
                  onClick={onClose}
                  colorScheme="blue"
                />
              </HStack>
              <VStack align="stretch" spacing={4}>
                <Heading size="md" color="gray.800">
                  {title}
                </Heading>
                <Box color="gray.800">{content}</Box>
              </VStack>
            </Box>
          </Box>
        </Portal>
      )}
    </>
  );
};
